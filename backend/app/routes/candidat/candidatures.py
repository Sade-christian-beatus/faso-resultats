import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_current_profil_candidat
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.candidature import Candidature, MethodeVerification, StatutVerificationCandidature
from app.models.journal_consultation_profil import ActionJournalConsultation
from app.models.profil_candidat import ProfilCandidat
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

_MAX_REJETS_PAR_JOUR = 5


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
    if await _rejets_aujourdhui(db, profil.id) >= _MAX_REJETS_PAR_JOUR:
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
async def confirmer_otp(
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
