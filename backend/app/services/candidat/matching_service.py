from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_deterministe
from app.models import Examen, Resultat, StatutExamen
from app.models.candidature import Candidature, MethodeVerification, StatutVerificationCandidature
from app.models.profil_candidat import ProfilCandidat
from app.services.candidat.notification_engine import NotificationEngine
from app.services.candidat.verification_service import DecisionVerification, VerificationService


class MatchingService:
    """Rapproche le profil candidat (plateforme) des résultats publiés par les
    administrations (tenants) — docs/PROFIL_CANDIDAT_UNIFIE.md § 4.5, § 6."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def matcher_retroactif(self, profil: ProfilCandidat) -> list[Candidature]:
        """Scénario B (§ 4.5) : à la création d'un profil, cherche dans tous les tenants
        les résultats déjà publiés qui portent son CNIB, et crée les candidatures
        correspondantes automatiquement. Aucune notification : ce sont des résultats
        déjà anciens, pas de raison de spammer."""
        query = (
            select(Resultat)
            .join(Examen, Examen.id == Resultat.examen_id)
            .where(Examen.statut == StatutExamen.PUBLISHED, Resultat.numero_cnib.isnot(None))
        )
        resultats = (await self.db.execute(query)).scalars().all()

        candidatures_creees: list[Candidature] = []
        for resultat in resultats:
            if hash_deterministe(resultat.numero_cnib) != profil.numero_cnib_hash:
                continue

            recepisse = resultat.numero_recepisse or resultat.numero_pv
            deja_liee = await self.db.execute(
                select(Candidature).where(
                    Candidature.administration_id == resultat.administration_id,
                    Candidature.numero_recepisse == recepisse,
                )
            )
            if deja_liee.scalars().first() is not None:
                continue

            candidature = Candidature(
                profil_candidat_id=profil.id,
                administration_id=resultat.administration_id,
                examen_id=resultat.examen_id,
                numero_recepisse=recepisse,
                statut_verification=StatutVerificationCandidature.VERIFIE_AUTO,
                methode_verification=MethodeVerification.CNIB_MATCH_AUTO,
                date_verification=datetime.now(UTC),
                dernier_resultat_id=resultat.id,
                dernier_resultat_phase=resultat.phase.value,
                dernier_resultat_statut=resultat.decision,
            )
            self.db.add(candidature)
            candidatures_creees.append(candidature)

        return candidatures_creees

    async def traiter_publication_examen(self, examen: Examen) -> None:
        """Scénario A (§ 4.5) / Événement 1 (§ 6) : à la publication d'un examen, tente
        de vérifier les candidatures en attente qui le concernent, met à jour leur cache
        de résultat, et notifie les candidats dont le résultat vient d'apparaître."""
        candidatures = (
            (
                await self.db.execute(
                    select(Candidature).where(
                        Candidature.examen_id == examen.id,
                        Candidature.statut_verification == StatutVerificationCandidature.EN_ATTENTE,
                    )
                )
            )
            .scalars()
            .all()
        )
        if not candidatures:
            return

        verification_service = VerificationService(self.db)
        for candidature in candidatures:
            profil = await self.db.get(ProfilCandidat, candidature.profil_candidat_id)
            if profil is None:
                continue

            decision, methode, resultat = await verification_service.verifier(
                profil,
                candidature.administration_id,
                candidature.examen_id,
                candidature.numero_recepisse,
            )

            if decision == DecisionVerification.REJETEE:
                candidature.statut_verification = StatutVerificationCandidature.REJETE
                continue
            if decision == DecisionVerification.OTP_REQUIS:
                candidature.methode_verification = MethodeVerification.OTP_SMS
                continue
            if decision != DecisionVerification.VERIFIEE or resultat is None:
                continue  # toujours pas publié pour ce récépissé précis

            candidature.statut_verification = StatutVerificationCandidature.VERIFIE_AUTO
            candidature.methode_verification = methode
            candidature.date_verification = datetime.now(UTC)

            resultat_deja_notifie = (
                candidature.dernier_resultat_id == resultat.id
                and candidature.derniere_notification_envoyee is not None
            )
            candidature.dernier_resultat_id = resultat.id
            candidature.dernier_resultat_phase = resultat.phase.value
            candidature.dernier_resultat_statut = resultat.decision

            if resultat_deja_notifie or not candidature.notifications_activees:
                continue
            if not profil.notifications_sms:
                continue

            message = NotificationEngine.formater_message_resultat(examen, resultat)
            if await NotificationEngine.envoyer_sms(profil.telephone, message):
                candidature.derniere_notification_envoyee = datetime.now(UTC)
