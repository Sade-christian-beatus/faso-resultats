import uuid
from datetime import UTC, date, datetime

from app.models import Examen, Ingestion, Resultat
from app.services.phases import phase_suivante_attendue


def construire_resultats(ingestion: Ingestion, examen: Examen) -> list[Resultat]:
    """Transforme l'aperçu validé d'une ingestion en lignes Resultat prêtes à publier.
    Suppose que l'appelant a déjà vérifié qu'aucune ligne ne porte d'erreur et que la
    phase de l'ingestion est ouverte (app/services/phases.py).
    """
    publiee_at = datetime.now(UTC)
    resultats = []
    for ligne in ingestion.apercu_donnees:
        donnees = ligne["donnees"]
        date_naissance = (
            date.fromisoformat(donnees["date_naissance"]) if donnees.get("date_naissance") else None
        )
        resultats.append(
            Resultat(
                id=uuid.uuid4(),
                administration_id=ingestion.administration_id,
                examen_id=ingestion.examen_id,
                ingestion_id=ingestion.id,
                numero_pv=donnees["numero_pv"],
                jury=donnees["jury"],
                nom=donnees["nom"],
                prenom=donnees["prenom"],
                date_naissance=date_naissance,
                lieu_naissance=donnees.get("lieu_naissance"),
                etablissement=donnees.get("etablissement"),
                numero_cnib=donnees.get("numero_cnib"),
                numero_recepisse=donnees.get("numero_recepisse"),
                code_concours=donnees.get("code_concours"),
                code_centre=donnees.get("code_centre"),
                rang_numerique=donnees.get("rang_numerique"),
                rang_affiche=donnees.get("rang_affiche"),
                decision=donnees["decision"],
                moyenne=donnees.get("moyenne"),
                phase=ingestion.phase,
                date_publication_phase=publiee_at,
                phase_suivante_attendue=phase_suivante_attendue(
                    examen, ingestion.phase, donnees["decision"]
                ),
                donnees_brutes=ligne["brut"],
            )
        )
    return resultats
