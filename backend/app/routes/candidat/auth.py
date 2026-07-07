from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import get_settings
from app.core.cache import cache_delete, cache_get, cache_set
from app.core.deps import get_current_profil_candidat
from app.core.rate_limit import limiter
from app.core.security import hash_deterministe
from app.database import get_db
from app.models.journal_consultation_profil import ActionJournalConsultation
from app.models.profil_candidat import ProfilCandidat, StatutProfilCandidat
from app.schemas.candidat import (
    InscriptionRequest,
    InscriptionResponse,
    LoginRequest,
    LoginResponse,
    OtpVerifyRequest,
    ProfilCandidatOut,
    ProfilCandidatUpdate,
    SessionResponse,
)
from app.services.candidat.auth_service import AuthCandidatService
from app.services.candidat.journal_service import journaliser
from app.services.candidat.matching_service import MatchingService
from app.services.candidat.notification_engine import NotificationEngine

router = APIRouter(prefix="/api/v1/candidat", tags=["candidat"])
settings = get_settings()

_PREFIXE_INSCRIPTION_ATTENTE = "candidat:inscription_attente:"


def _cle_inscription_attente(telephone: str) -> str:
    return f"{_PREFIXE_INSCRIPTION_ATTENTE}{telephone}"


@router.post(
    "/inscription",
    response_model=InscriptionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Créer un espace candidat",
    description="Étapes 1 à 5 du parcours d'inscription (docs/PROFIL_CANDIDAT_UNIFIE.md "
    "§ 4.1) : envoie un code OTP par SMS pour confirmer le numéro de téléphone. Le "
    "compte n'est créé qu'après validation du code via POST /otp/verify.",
)
@limiter.limit(settings.rate_limit_login)
async def inscription(
    request: Request, payload: InscriptionRequest, db: AsyncSession = Depends(get_db)
) -> InscriptionResponse:
    cnib_hash = hash_deterministe(payload.numero_cnib)
    telephone_hash = hash_deterministe(payload.telephone)

    existant = await db.execute(
        select(ProfilCandidat).where(
            (ProfilCandidat.numero_cnib_hash == cnib_hash)
            | (ProfilCandidat.telephone_hash == telephone_hash)
        )
    )
    if existant.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec ce numéro CNIB ou ce numéro de téléphone",
        )

    code = await AuthCandidatService.generer_otp(payload.telephone)
    if code is not None:
        # Numéro non verrouillé : mémorise les données d'inscription en attente de
        # confirmation OTP. Si verrouillé (code=None), ne rien stocker — la tentative
        # ne peut de toute façon pas aboutir pendant la fenêtre de verrouillage.
        await cache_set(
            _cle_inscription_attente(payload.telephone),
            {
                "numero_cnib": payload.numero_cnib,
                "nom_complet": payload.nom_complet,
                "date_naissance": payload.date_naissance.isoformat(),
                "telephone": payload.telephone,
                "consentement_apdp_version": payload.consentement_apdp_version,
            },
            ttl_secondes=settings.candidat_otp_expire_minutes * 60,
        )

    return InscriptionResponse(
        message="Un code de vérification a été envoyé par SMS.",
        expire_dans_minutes=settings.candidat_otp_expire_minutes,
        code_otp_debug=code if settings.environment != "production" else None,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Demander un code de connexion",
    description="Envoie un code OTP par SMS si un compte actif existe pour ce numéro. "
    "Réponse volontairement générique dans tous les cas, pour ne pas permettre "
    "l'énumération des numéros de téléphone inscrits.",
)
@limiter.limit(settings.rate_limit_login)
async def login(
    request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    telephone_hash = hash_deterministe(payload.telephone)
    result = await db.execute(
        select(ProfilCandidat).where(ProfilCandidat.telephone_hash == telephone_hash)
    )
    profil = result.scalar_one_or_none()

    code_debug = None
    if profil is not None and profil.statut == StatutProfilCandidat.ACTIF:
        code = await AuthCandidatService.generer_otp(payload.telephone)
        code_debug = code if settings.environment != "production" else None

    return LoginResponse(
        message="Si un compte existe pour ce numéro, un code a été envoyé par SMS.",
        code_otp_debug=code_debug,
    )


@router.post(
    "/otp/verify",
    response_model=SessionResponse,
    summary="Valider le code OTP",
    description="Termine soit une inscription en attente (le compte est créé), soit "
    "une connexion à un compte existant. Renvoie un token de session candidat.",
)
@limiter.limit(settings.rate_limit_login)
async def otp_verify(
    request: Request, payload: OtpVerifyRequest, db: AsyncSession = Depends(get_db)
) -> SessionResponse:
    if not await AuthCandidatService.verifier_otp(payload.telephone, payload.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Code invalide ou expiré"
        )

    inscription_attente = await cache_get(_cle_inscription_attente(payload.telephone))
    if inscription_attente is not None:
        profil = ProfilCandidat(
            numero_cnib=inscription_attente["numero_cnib"],
            numero_cnib_hash=hash_deterministe(inscription_attente["numero_cnib"]),
            nom_complet=inscription_attente["nom_complet"],
            date_naissance=inscription_attente["date_naissance"],
            telephone=inscription_attente["telephone"],
            telephone_hash=hash_deterministe(inscription_attente["telephone"]),
            telephone_verifie=True,
            consentement_apdp_date=datetime.now(UTC),
            consentement_apdp_version=inscription_attente["consentement_apdp_version"],
        )
        db.add(profil)
        await db.flush()
        await journaliser(db, profil.id, ActionJournalConsultation.INSCRIPTION, request)
        # Scénario B (§ 4.5) : rapproche immédiatement les résultats déjà publiés qui
        # portent le CNIB du candidat, sans notification (pas de spam pour du passé).
        await MatchingService(db).matcher_retroactif(profil)
        await db.commit()
        await db.refresh(profil)
        await cache_delete(_cle_inscription_attente(payload.telephone))

        # Atténuation prise de contrôle de compte (§ 8, risque 2) : le titulaire du
        # téléphone est notifié immédiatement, qu'il soit ou non l'auteur de l'inscription.
        await NotificationEngine.envoyer_sms(
            profil.telephone, NotificationEngine.formater_message_alerte_creation_compte()
        )

        token = AuthCandidatService.creer_session(profil.id)
        return SessionResponse(access_token=token, compte_cree=True)

    telephone_hash = hash_deterministe(payload.telephone)
    result = await db.execute(
        select(ProfilCandidat).where(ProfilCandidat.telephone_hash == telephone_hash)
    )
    profil = result.scalar_one_or_none()
    if profil is None or profil.statut != StatutProfilCandidat.ACTIF:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable")

    profil.derniere_connexion = func.now()
    await journaliser(db, profil.id, ActionJournalConsultation.LOGIN, request)
    await db.commit()

    token = AuthCandidatService.creer_session(profil.id)
    return SessionResponse(access_token=token, compte_cree=False)


@router.get(
    "/me",
    response_model=ProfilCandidatOut,
    summary="Profil du candidat connecté",
)
async def me(
    request: Request,
    profil: ProfilCandidat = Depends(get_current_profil_candidat),
    db: AsyncSession = Depends(get_db),
) -> ProfilCandidat:
    await journaliser(db, profil.id, ActionJournalConsultation.VIEW_DASHBOARD, request)
    await db.commit()
    return profil


@router.patch(
    "/me",
    response_model=ProfilCandidatOut,
    summary="Mettre à jour les préférences du candidat connecté",
    description="Email et préférences de notification uniquement — les données "
    "d'identité (CNIB, nom, date de naissance) ne sont pas modifiables ici.",
)
async def update_me(
    request: Request,
    payload: ProfilCandidatUpdate,
    profil: ProfilCandidat = Depends(get_current_profil_candidat),
    db: AsyncSession = Depends(get_db),
) -> ProfilCandidat:
    updates = payload.model_dump(exclude_unset=True)
    for champ, valeur in updates.items():
        setattr(profil, champ, valeur)

    await journaliser(db, profil.id, ActionJournalConsultation.UPDATE_PREFERENCES, request)
    await db.commit()
    await db.refresh(profil)
    return profil


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer son compte (droit à l'oubli)",
    description="Supprime immédiatement le profil, ses candidatures et son journal de "
    "consultation (docs/PROFIL_CANDIDAT_UNIFIE.md § 7). N'affecte pas les résultats "
    "publiés par les administrations.",
)
async def delete_me(
    profil: ProfilCandidat = Depends(get_current_profil_candidat),
    db: AsyncSession = Depends(get_db),
) -> None:
    await db.delete(profil)
    await db.commit()
