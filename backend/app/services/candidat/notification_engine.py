import logging
from datetime import UTC, datetime

from app.models import Examen, Resultat

logger = logging.getLogger(__name__)

_HEURE_DEBUT_SILENCE = 22
_HEURE_FIN_SILENCE = 6


class NotificationEngine:
    """Moteur de notifications (docs/PROFIL_CANDIDAT_UNIFIE.md § 6). L'envoi SMS est un
    stub en Phase 1 : il journalise l'intention d'envoi sans appeler de fournisseur réel
    — l'intégration Orange/Moov/Telecel est prévue en Phase 2 (voir CLAUDE.md, roadmap).

    Limite connue : sans file de tâches (RQ, Phase 2), une notification tombant dans la
    plage silencieuse (22h-6h) est simplement abandonnée plutôt que reportée — il n'y a
    pas encore de mécanisme de nouvelle tentative différée."""

    @staticmethod
    def _dans_plage_silencieuse(maintenant: datetime) -> bool:
        heure = maintenant.hour
        return heure >= _HEURE_DEBUT_SILENCE or heure < _HEURE_FIN_SILENCE

    @staticmethod
    def formater_message_resultat(examen: Examen, resultat: Resultat) -> str:
        recepisse = resultat.numero_recepisse or resultat.numero_pv
        message = (
            f"Faso Resultats: resultat publie pour {examen.libelle} "
            f"(recepisse {recepisse}) : {resultat.decision}. "
            f"Details: fasoresultats.bf/r/{recepisse}"
        )
        return message[:160]

    @staticmethod
    async def envoyer_sms(telephone: str, message: str) -> bool:
        """Renvoie True si le SMS a été (simulé comme) envoyé. Ne journalise jamais le
        numéro complet, conformément à CLAUDE.md (« aucun log de données personnelles
        sensibles »)."""
        if NotificationEngine._dans_plage_silencieuse(datetime.now(UTC)):
            logger.info("SMS différé (plage silencieuse 22h-6h) pour ...%s", telephone[-4:])
            return False
        logger.info("[SMS stub] vers ...%s: %s", telephone[-4:], message)
        return True
