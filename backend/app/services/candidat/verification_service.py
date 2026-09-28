import enum
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Examen, Resultat, StatutExamen
from app.models.candidature import MethodeVerification, StatutVerificationCandidature
from app.models.profil_candidat import ProfilCandidat


def _identite_correspond(resultat: Resultat, profil: ProfilCandidat) -> bool:
    if resultat.numero_cnib_hash:
        return resultat.numero_cnib_hash == profil.numero_cnib_hash
    if resultat.date_naissance:
        return resultat.date_naissance.isoformat() == profil.date_naissance
    return False


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

    async def _trouver_resultats_publies(
        self, administration_id: uuid.UUID, examen_id: uuid.UUID, numero_recepisse: str
    ) -> list[Resultat]:
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
        return list((await self.db.execute(query)).scalars().all())

    async def trouver_resultat_publie(
        self,
        administration_id: uuid.UUID,
        examen_id: uuid.UUID,
        numero_recepisse: str,
        profil: ProfilCandidat | None = None,
    ) -> Resultat | None:
        """`numero_pv` n'est unique que par (`examen_id`, `jury`) : plusieurs jurys du
        même examen peuvent réutiliser le même numéro. S'il n'y a qu'un seul résultat
        correspondant, pas d'ambiguïté. S'il y en a plusieurs, on ne peut pas deviner
        lequel appartient au candidat sans risquer de renvoyer celui d'un autre —
        on ne retient que celui confirmé sans équivoque par CNIB/date de naissance
        (si `profil` est fourni) ; sinon on ne renvoie rien plutôt qu'un choix arbitraire.
        """
        resultats = await self._trouver_resultats_publies(
            administration_id, examen_id, numero_recepisse
        )
        if not resultats:
            return None
        if len(resultats) == 1:
            return resultats[0]
        if profil is None:
            return None
        confirmes = [r for r in resultats if _identite_correspond(r, profil)]
        return confirmes[0] if len(confirmes) == 1 else None

    async def verifier(
        self,
        profil: ProfilCandidat,
        administration_id: uuid.UUID,
        examen_id: uuid.UUID,
        numero_recepisse: str,
    ) -> tuple[DecisionVerification, MethodeVerification | None, Resultat | None]:
        resultats = await self._trouver_resultats_publies(
            administration_id, examen_id, numero_recepisse
        )
        if not resultats:
            return DecisionVerification.EN_ATTENTE, None, None

        if len(resultats) > 1:
            confirmes = [r for r in resultats if _identite_correspond(r, profil)]
            if len(confirmes) == 1:
                resultat = confirmes[0]
                methode = (
                    MethodeVerification.CNIB_MATCH_AUTO
                    if resultat.numero_cnib_hash
                    else MethodeVerification.DATE_NAISSANCE
                )
                return DecisionVerification.VERIFIEE, methode, resultat
            # Plusieurs jurys partagent ce numéro et aucun résultat ne peut être
            # confirmé sans équivoque : fallback OTP obligatoire, jamais de choix au
            # hasard entre les candidats.
            return DecisionVerification.OTP_REQUIS, None, None

        resultat = resultats[0]
        if resultat.numero_cnib_hash:
            if resultat.numero_cnib_hash == profil.numero_cnib_hash:
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
