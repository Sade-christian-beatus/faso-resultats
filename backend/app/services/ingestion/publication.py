import uuid
from datetime import UTC, date, datetime
from typing import Any

from app.models import Examen, Ingestion, Resultat
from app.services.ingestion.normalizer import normaliser_donnees
from app.services.phases import phase_suivante_attendue


class LignesInvalidesError(ValueError):
    """Some preview rows do not pass validation: nothing may be published."""

    def __init__(self, nombre_lignes: int) -> None:
        super().__init__(f"{nombre_lignes} ligne(s) invalide(s)")
        self.nombre_lignes = nombre_lignes


def _normaliser_apercu(apercu_donnees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Canonical data of every preview row, revalidated at publication time rather than
    trusting `nombre_erreurs`: what is published is exactly what passes validation
    (audit 2026-11-16, C1/E5 — values stored in an older format or sent by a client could
    otherwise reach the database and fail there with a 500). Raises
    `LignesInvalidesError` if any row is invalid."""
    normalisees = [normaliser_donnees(ligne["donnees"]) for ligne in apercu_donnees]
    nombre_invalides = sum(1 for ligne in normalisees if ligne.erreurs)
    if nombre_invalides:
        raise LignesInvalidesError(nombre_invalides)
    return [ligne.donnees for ligne in normalisees]


def construire_resultats(ingestion: Ingestion, examen: Examen) -> list[Resultat]:
    """Transforme l'aperçu validé d'une ingestion en lignes Resultat prêtes à publier.
    Suppose que l'appelant a déjà vérifié que la phase de l'ingestion est ouverte
    (app/services/phases.py). Lève `LignesInvalidesError` si une ligne est invalide.
    """
    publiee_at = datetime.now(UTC)
    lignes_donnees = _normaliser_apercu(ingestion.apercu_donnees)
    resultats = []
    for ligne, donnees in zip(ingestion.apercu_donnees, lignes_donnees, strict=True):
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
