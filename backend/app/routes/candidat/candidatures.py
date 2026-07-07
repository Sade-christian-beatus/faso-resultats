import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_current_profil_candidat
from app.core.rate_limit import limiter
from app.database import get_db
from app.models import Administration, Examen, StatutAdministration, StatutExamen
from app.models.candidature import Candidature, MethodeVerification, StatutVerificationCandidature
from app.models.journal_consultation_profil import ActionJournalConsultation
from app.models.profil_candidat import ProfilCandidat, StatutProfilCandidat
from app.schemas.candidat import (
    CandidatureCreate,
    CandidatureOtpConfirmRequest,
    CandidatureOut,
)
from app.services.candidat.auth_service import AuthCandidatService
from app.services.candidat.journal_service import journaliser
from app.services.candidat.verification_service import DecisionVerification, VerificationService

router = APIRouter(prefix="/api/v1/candidat/candidatures", tags=["candidat"])
settings = get_settings()


async def _rejets_aujourdhui(db: AsyncSession, profil_id: uuid.UUID) -> int:
    depuis = datetime.now(UTC) - timedelta(days=1)
    result = await db.execute(
        select(func.count()).where(
            Candidature.profil_candidat_id == profil_id,
            Candidature.statut_verification == StatutVerificationCandidature.REJETE,
            Candidature.created_at >= depuis,
        )
    )
    return result.scalar_one()


async def _verifier_et_suspendre_si_abus(db: AsyncSession, profil: ProfilCandidat) -> None:
    """Détection d'abus (docs/PROFIL_CANDIDAT_UNIFIE.md § 8) : au-delà d'un nombre
    minimal de tentatives, un taux de rejet trop élevé suggère un compte qui accumule
    des récépissés qui ne lui appartiennent pas — suspension automatique."""
    total = (
        await db.execute(select(func.count()).where(Candidature.profil_candidat_id == profil.id))
    ).scalar_one()
    if total < settings.candidat_abus_minimum_tentatives:
        return

    rejets = (
        await db.execute(
            select(func.count()).where(
                Candidature.profil_candidat_id == profil.id,
                Candidature.statut_verification == StatutVerificationCandidature.REJETE,
            )
        )
    ).scalar_one()
    if rejets / total > settings.candidat_abus_taux_rejet_suspension:
        profil.statut = StatutProfilCandidat.SUSPENDU


async def _administration_et_examen_existent(
    db: AsyncSession, administration_id: uuid.UUID, examen_id: uuid.UUID
) -> bool:
    """Candidature.administration_id/examen_id ne sont pas des FK (schéma plateforme
    volontairement indépendant des schémas tenants, voir docs/MULTI_TENANCY.md) : sans
    ce contrôle applicatif, un candidat pourrait créer des candidatures orphelines
    référençant des UUID inexistants."""
    # ACTIF et PILOTE sont tous deux des statuts opérationnels (voir seed.py : les 3
    # administrations de démonstration OCECOS/Office du BAC/AGRE sont PILOTE par
    # défaut) — seuls SUSPENDU et RESILIE bloquent l'ajout d'une candidature.
    administration = await db.get(Administration, administration_id)
    if administration is None or administration.statut in (
        StatutAdministration.SUSPENDU,
        StatutAdministration.RESILIE,
    ):
        return False

    examen = await db.get(Examen, examen_id)
    if (
        examen is None
        or examen.administration_id != administration_id
        or examen.statut not in (StatutExamen.PUBLISHED, StatutExamen.DRAFT)
    ):
        return False

    return True


@router.get(
    "",
    response_model=list[CandidatureOut],
    summary="Dashboard candidat",
    description="Liste les candidatures du candidat connecté, tous tenants confondus.",
)
async def list_candidatures(
    request: Request,
    profil: ProfilCandidat = Depends(get_current_profil_candidat),
    db: AsyncSession = Depends(get_db),
) -> list[Candidature]:
    result = await db.execute(
        select(Candidature)
        .where(
            Candidature.profil_candidat_id == profil.id,
            Candidature.statut_verification != StatutVerificationCandidature.REJETE,
        )
        .order_by(Candidature.created_at.desc())
    )
    await journaliser(db, profil.id, ActionJournalConsultation.VIEW_DASHBOARD, request)
    await db.commit()
    return list(result.scalars().all())


@router.post(
    "",
    response_model=CandidatureOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter une candidature",
    description="Vérifie la propriété du récépissé dans l'ordre CNIB automatique → date "
    "de naissance → confirmation OTP (docs/PROFIL_CANDIDAT_UNIFIE.md § 5). Si l'examen "
    "n'est pas encore publié, la candidature reste en attente et sera vérifiée "
    "automatiquement à la publication.",
)
@limiter.limit(settings.rate_limit_login)
async def create_candidature(
    request: Request,
    payload: CandidatureCreate,
    profil: ProfilCandidat = Depends(get_current_profil_candidat),
    db: AsyncSession = Depends(get_db),
) -> Candidature:
    if not await _administration_et_examen_existent(
        db, payload.administration_id, payload.examen_id
    ):
        raise HTTPException(status_code=404, detail="Administration ou examen introuvable")

    if await _rejets_aujourdhui(db, profil.id) >= settings.candidat_abus_seuil_rejets_par_jour:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives infructueuses aujourd'hui. Réessayez demain ou "
            "contactez le support.",
        )

    existante = await db.execute(
        select(Candidature).where(
            Candidature.administration_id == payload.administration_id,
            Candidature.numero_recepisse == payload.numero_recepisse,
        )
    )
    if existante.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce récépissé est déjà rattaché à un compte candidat",
        )

    decision, methode, resultat = await VerificationService(db).verifier(
        profil, payload.administration_id, payload.examen_id, payload.numero_recepisse
    )

    if decision == DecisionVerification.REJETEE:
        db.add(
            Candidature(
                profil_candidat_id=profil.id,
                administration_id=payload.administration_id,
                examen_id=payload.examen_id,
                numero_recepisse=payload.numero_recepisse,
                statut_verification=StatutVerificationCandidature.REJETE,
            )
        )
        await db.flush()
        await _verifier_et_suspendre_si_abus(db, profil)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ce récépissé ne correspond pas à votre identité. Vérifiez le numéro "
            "saisi ou contactez le support.",
        )

    candidature = Candidature(
        profil_candidat_id=profil.id,
        administration_id=payload.administration_id,
        examen_id=payload.examen_id,
        numero_recepisse=payload.numero_recepisse,
        statut_verification=StatutVerificationCandidature.EN_ATTENTE,
    )

    if decision == DecisionVerification.VERIFIEE:
        candidature.statut_verification = StatutVerificationCandidature.VERIFIE_AUTO
        candidature.methode_verification = methode
        candidature.date_verification = datetime.now(UTC)
        if resultat is not None:
            candidature.dernier_resultat_id = resultat.id
            candidature.dernier_resultat_phase = resultat.phase.value
            candidature.dernier_resultat_statut = resultat.decision
    elif decision == DecisionVerification.OTP_REQUIS:
        # Aucune donnée exploitable dans le résultat publié : fallback OTP envoyé sur le
        # téléphone du profil, à confirmer via POST .../{id}/confirmer-otp.
        candidature.methode_verification = MethodeVerification.OTP_SMS
        await AuthCandidatService.generer_otp(profil.telephone)

    db.add(candidature)
    await journaliser(db, profil.id, ActionJournalConsultation.ADD_CANDIDATURE, request)
    await db.commit()
    await db.refresh(candidature)
    return candidature


@router.post(
    "/{candidature_id}/confirmer-otp",
    response_model=CandidatureOut,
    summary="Confirmer une candidature par OTP (mécanisme 3, fallback)",
    description="Utilisé quand ni le CNIB ni la date de naissance ne figurent dans le "
    "résultat publié : confirme la propriété du récépissé par un code envoyé au "
    "candidat lui-même, plutôt qu'une correspondance automatique.",
)
@limiter.limit(settings.rate_limit_login)
async def confirmer_otp(
    request: Request,
    candidature_id: uuid.UUID,
    payload: CandidatureOtpConfirmRequest,
    profil: ProfilCandidat = Depends(get_current_profil_candidat),
    db: AsyncSession = Depends(get_db),
) -> Candidature:
    candidature = await db.get(Candidature, candidature_id)
    if candidature is None or candidature.profil_candidat_id != profil.id:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    if candidature.methode_verification != MethodeVerification.OTP_SMS:
        raise HTTPException(
            status_code=409, detail="Cette candidature n'attend pas de confirmation OTP"
        )

    if not await AuthCandidatService.verifier_otp(profil.telephone, payload.code):
        raise HTTPException(status_code=401, detail="Code invalide ou expiré")

    candidature.statut_verification = StatutVerificationCandidature.VERIFIE_MANUEL
    candidature.methode_verification = MethodeVerification.VALIDATION_MANUELLE
    candidature.date_verification = datetime.now(UTC)
    await db.commit()
    await db.refresh(candidature)
    return candidature


@router.delete(
    "/{candidature_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retirer une candidature",
)
async def delete_candidature(
    candidature_id: uuid.UUID,
    request: Request,
    profil: ProfilCandidat = Depends(get_current_profil_candidat),
    db: AsyncSession = Depends(get_db),
) -> None:
    candidature = await db.get(Candidature, candidature_id)
    if candidature is None or candidature.profil_candidat_id != profil.id:
        raise HTTPException(status_code=404, detail="Candidature introuvable")

    await db.delete(candidature)
    await journaliser(db, profil.id, ActionJournalConsultation.DELETE_CANDIDATURE, request)
    await db.commit()
