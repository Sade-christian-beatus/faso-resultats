import enum
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_deterministe
from app.models import Examen, Resultat, StatutExamen
from app.models.candidature import MethodeVerification, StatutVerificationCandidature
from app.models.profil_candidat import ProfilCandidat


class DecisionVerification(str, enum.Enum):
    """Issue de la tentative de vérification (docs/PROFIL_CANDIDAT_UNIFIE.md § 5)."""

    VERIFIEE = "VERIFIEE"  # correspondance CNIB ou date de naissance
    REJETEE = "REJETEE"  # une donnée de vérification était disponible mais ne correspond pas
    OTP_REQUIS = "OTP_REQUIS"  # aucune donnée de vérification disponible : fallback OTP
    EN_ATTENTE = "EN_ATTENTE"  # l'examen n'est pas encore publié, rien à vérifier pour l'instant


class VerificationService:
    """Vérifie qu'un candidat est bien le propriétaire du récépissé qu'il déclare,
    dans l'ordre de préférence de la § 5 : CNIB automatique → date de naissance →
    fallback OTP (géré par l'appelant, ce service se contente de signaler qu'il est
    nécessaire)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def trouver_resultat_publie(
        self, administration_id: uuid.UUID, examen_id: uuid.UUID, numero_recepisse: str
    ) -> Resultat | None:
        query = (
            select(Resultat)
            .join(Examen, Examen.id == Resultat.examen_id)
            .where(
                Resultat.administration_id == administration_id,
                Resultat.examen_id == examen_id,
                Examen.statut == StatutExamen.PUBLISHED,
                (Resultat.numero_recepisse == numero_recepisse)
                | (Resultat.numero_pv == numero_recepisse),
            )
        )
        return (await self.db.execute(query)).scalars().first()

    async def verifier(
        self,
        profil: ProfilCandidat,
        administration_id: uuid.UUID,
        examen_id: uuid.UUID,
        numero_recepisse: str,
    ) -> tuple[DecisionVerification, MethodeVerification | None, Resultat | None]:
        resultat = await self.trouver_resultat_publie(
            administration_id, examen_id, numero_recepisse
        )
        if resultat is None:
            return DecisionVerification.EN_ATTENTE, None, None

        if resultat.numero_cnib:
            if hash_deterministe(resultat.numero_cnib) == profil.numero_cnib_hash:
                return DecisionVerification.VERIFIEE, MethodeVerification.CNIB_MATCH_AUTO, resultat
            return DecisionVerification.REJETEE, None, resultat

        if resultat.date_naissance:
            if resultat.date_naissance.isoformat() == profil.date_naissance:
                return DecisionVerification.VERIFIEE, MethodeVerification.DATE_NAISSANCE, resultat
            return DecisionVerification.REJETEE, None, resultat

        return DecisionVerification.OTP_REQUIS, None, resultat

    @staticmethod
    def statut_pour_decision(decision: DecisionVerification) -> StatutVerificationCandidature:
        return {
            DecisionVerification.VERIFIEE: StatutVerificationCandidature.VERIFIE_AUTO,
            DecisionVerification.REJETEE: StatutVerificationCandidature.REJETE,
            DecisionVerification.OTP_REQUIS: StatutVerificationCandidature.EN_ATTENTE,
            DecisionVerification.EN_ATTENTE: StatutVerificationCandidature.EN_ATTENTE,
        }[decision]
