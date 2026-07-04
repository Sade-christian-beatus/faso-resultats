"""Abstraction unifiant la récupération des résultats depuis n'importe quelle source
gouvernementale existante (upload manuel, API partenaire, scraping de PDF ou de
réseaux sociaux, suivi de presse). Voir `docs/CONTEXTE_METIER.md` § 4.2 : chaque canal
de publication déjà utilisé par un ministère (fonction-publique.gov.bf,
securite.gov.bf, SIGEC-CEP, Facebook, RTB/Sidwaya) peut potentiellement être branché
ici sans changer le reste du pipeline d'ingestion.

Seule `FileImportSource` est implémentée en Phase 1 (upload manuel — cœur stratégique
du projet, voir § 1). Les autres sources ci-dessous sont des classes documentées mais
non implémentées : leur mise en œuvre dépend d'analyses juridiques, techniques et de
partenariats à établir avant tout déploiement.
"""

from abc import ABC, abstractmethod

from app.services.ingestion.types import LigneExtraite


class ResultsSource(ABC):
    """Interface commune à toutes les sources de résultats."""

    @abstractmethod
    async def fetch_results(self, examen_id: str, **kwargs) -> list[LigneExtraite]:
        """Retourne les lignes de résultats brutes disponibles pour un examen donné.
        Les paramètres additionnels (`**kwargs`) sont spécifiques à chaque source
        (ex. chemin de fichier pour un import manuel, jeton d'API pour SIGEC)."""
        ...
