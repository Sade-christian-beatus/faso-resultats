from pathlib import Path

from app.models import TypeFichier
from app.services.ingestion.dispatch import parser_fichier
from app.services.ingestion.types import LigneExtraite
from app.services.sources.base import ResultsSource


class FileImportSource(ResultsSource):
    """Ingestion par upload manuel de fichiers Excel/PDF (natif ou scanné, détecté
    automatiquement) — seule source réellement utilisée en Phase 1, et cœur
    stratégique du projet (`docs/CONTEXTE_METIER.md` § 1 : la qualité et la vitesse
    du pipeline d'ingestion sont l'avantage compétitif principal face aux PDF
    illisibles publiés par les ministères).

    Délègue à `app.services.ingestion.dispatch.parser_fichier`, déjà utilisé
    directement par `POST /api/v1/admin/ingestions`. Cette classe formalise
    seulement l'identité de « source » de ce chemin dans l'abstraction
    `ResultsSource`, sans remplacer la route existante ni son flux déjà testé
    upload → aperçu → correction → publication.
    """

    async def fetch_results(
        self,
        examen_id: str,
        *,
        chemin_fichier: str | Path,
        type_fichier: TypeFichier,
        decision_par_defaut: str | None = None,
    ) -> list[LigneExtraite]:
        # examen_id n'est pas utilisé ici : le parsing dépend uniquement du contenu du
        # fichier, l'association à l'examen se fait au niveau de la route d'upload.
        resultat = parser_fichier(chemin_fichier, type_fichier, decision_par_defaut)
        return resultat.lignes
