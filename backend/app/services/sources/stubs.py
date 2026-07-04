"""Sources documentées mais non implémentées — leur mise en œuvre dépend d'analyses
juridiques, techniques et de partenariats à établir avant tout déploiement (voir
`docs/CONTEXTE_METIER.md` § 4.2). Ne pas implémenter sans demande explicite.
"""

from app.services.ingestion.types import LigneExtraite
from app.services.sources.base import ResultsSource


class SigecApiSource(ResultsSource):
    """Consommation de l'API SIGEC-CEP (`resultats.examens.gov.bf`) si un partenariat
    officiel est conclu avec le MEBAPLN. À implémenter uniquement si un accord est
    signé — SIGEC-CEP est aujourd'hui un concurrent, pas un partenaire confirmé."""

    async def fetch_results(self, examen_id: str, **kwargs) -> list[LigneExtraite]:
        raise NotImplementedError(
            "SigecApiSource nécessite un partenariat officiel avec le MEBAPLN, non "
            "encore établi. Voir docs/CONTEXTE_METIER.md § 4.2."
        )


class GouvPdfMonitorSource(ResultsSource):
    """Surveillance automatique des publications PDF officielles. Les canaux à
    surveiller : `fonction-publique.gov.bf` (concours directs, professionnels,
    paramilitaires civils), `securite.gov.bf` (Police Nationale), `education.gov.bf`
    (annonces BEPC/BAC, souvent redirigeant vers PDF). Un scraper poli (respect
    robots.txt, délai entre requêtes) identifierait les nouveaux PDF et déclencherait
    le pipeline d'ingestion standard (`FileImportSource`) une fois le fichier
    téléchargé. À valider juridiquement avant activation."""

    async def fetch_results(self, examen_id: str, **kwargs) -> list[LigneExtraite]:
        raise NotImplementedError(
            "GouvPdfMonitorSource nécessite une validation juridique du scraping de "
            "sites gouvernementaux avant activation. Voir docs/CONTEXTE_METIER.md § 4.2."
        )


class FacebookMonitorSource(ResultsSource):
    """Surveillance de la page Facebook officielle du Ministère de la Sécurité
    (msecubf) qui publie régulièrement les résultats de la Police Nationale avec
    des liens de téléchargement. À évaluer : Graph API vs scraping, fiabilité,
    conformité aux CGU Facebook. Alternative pragmatique en attendant : monitoring
    manuel par un opérateur admin qui télécharge le PDF lié et l'importe via
    `FileImportSource`."""

    async def fetch_results(self, examen_id: str, **kwargs) -> list[LigneExtraite]:
        raise NotImplementedError(
            "FacebookMonitorSource nécessite une évaluation Graph API vs scraping et "
            "de la conformité aux CGU Facebook. Voir docs/CONTEXTE_METIER.md § 4.2."
        )


class PressMonitoringSource(ResultsSource):
    """Suivi des publications RTB et Sidwaya pour les résultats Armée/Gendarmerie,
    qui ne sont diffusés que par voie de presse — aucun canal en ligne n'existe pour
    ces corps. En pratique, un opérateur admin ingère manuellement les communiqués
    via `FileImportSource` ; cette classe formalise la traçabilité de cette source
    plutôt que d'automatiser un flux qui n'a pas de source numérique à surveiller."""

    async def fetch_results(self, examen_id: str, **kwargs) -> list[LigneExtraite]:
        raise NotImplementedError(
            "PressMonitoringSource n'a pas de source numérique à surveiller (Armée/"
            "Gendarmerie ne publient que par voie de presse) — ingestion manuelle "
            "via FileImportSource. Voir docs/CONTEXTE_METIER.md § 4.2."
        )
