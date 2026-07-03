import uuid
from datetime import date

from app.models import Ingestion, Resultat


def construire_resultats(ingestion: Ingestion) -> list[Resultat]:
    """Transforme l'aperçu validé d'une ingestion en lignes Resultat prêtes à publier.
    Suppose que l'appelant a déjà vérifié qu'aucune ligne ne porte d'erreur.
    """
    resultats = []
    for ligne in ingestion.apercu_donnees:
        donnees = ligne["donnees"]
        date_naissance = (
            date.fromisoformat(donnees["date_naissance"]) if donnees.get("date_naissance") else None
        )
        resultats.append(
            Resultat(
                id=uuid.uuid4(),
                examen_id=ingestion.examen_id,
                ingestion_id=ingestion.id,
                numero_pv=donnees["numero_pv"],
                jury=donnees["jury"],
                nom=donnees["nom"],
                prenom=donnees["prenom"],
                date_naissance=date_naissance,
                lieu_naissance=donnees.get("lieu_naissance"),
                etablissement=donnees.get("etablissement"),
                decision=donnees["decision"],
                moyenne=donnees.get("moyenne"),
                donnees_brutes=ligne["brut"],
            )
        )
    return resultats
