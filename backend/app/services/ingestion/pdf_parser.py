from pathlib import Path

import pdfplumber

from app.services.ingestion.normalizer import (
    colonnes_non_reconnues,
    construire_mapping_colonnes,
    message_colonnes_non_reconnues,
    normaliser_ligne,
)
from app.services.ingestion.types import LigneExtraite, ResultatExtraction


def parser_pdf(
    chemin_fichier: str | Path, decision_par_defaut: str | None = None
) -> ResultatExtraction:
    """Extrait les tableaux d'un PDF natif (texte, non scanné) via pdfplumber.
    La première ligne détectée sur la première table est l'en-tête.
    """
    lignes: list[LigneExtraite] = []
    mapping_colonnes: dict[str, str] | None = None
    numero_ligne = 2

    with pdfplumber.open(chemin_fichier) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table:
                    continue
                debut = 0
                if mapping_colonnes is None:
                    entetes = [str(c) if c is not None else "" for c in table[0]]
                    mapping_colonnes = construire_mapping_colonnes(entetes)
                    debut = 1

                for ligne_brute_liste in table[debut:]:
                    if all(v is None for v in ligne_brute_liste):
                        continue
                    ligne_brute = dict(zip(entetes, ligne_brute_liste, strict=False))
                    resultat = normaliser_ligne(ligne_brute, mapping_colonnes, decision_par_defaut)
                    lignes.append(
                        LigneExtraite(
                            ligne=numero_ligne,
                            donnees=resultat.donnees,
                            brut={k: v for k, v in ligne_brute.items() if k},
                            erreurs=resultat.erreurs,
                        )
                    )
                    numero_ligne += 1

    if mapping_colonnes is None:
        return ResultatExtraction(lignes=[], erreurs_fichier=["Aucun tableau détecté dans le PDF"])

    non_reconnues = colonnes_non_reconnues(entetes, mapping_colonnes)
    erreurs_fichier = [message_colonnes_non_reconnues(non_reconnues)] if non_reconnues else []
    return ResultatExtraction(lignes=lignes, erreurs_fichier=erreurs_fichier)
