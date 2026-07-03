from pathlib import Path

import openpyxl

from app.services.ingestion.normalizer import construire_mapping_colonnes, normaliser_ligne
from app.services.ingestion.types import LigneExtraite, ResultatExtraction, valeur_json_safe


def parser_excel(chemin_fichier: str | Path) -> ResultatExtraction:
    """Lit la première feuille d'un classeur Excel : la première ligne est l'en-tête,
    chaque ligne suivante est un résultat candidat.
    """
    classeur = openpyxl.load_workbook(chemin_fichier, data_only=True, read_only=True)
    feuille = classeur.active

    lignes_brutes = feuille.iter_rows(values_only=True)
    try:
        entetes = next(lignes_brutes)
    except StopIteration:
        return ResultatExtraction(lignes=[], erreurs_fichier=["Fichier vide"])

    entetes_str = [str(e) if e is not None else "" for e in entetes]
    mapping_colonnes = construire_mapping_colonnes(entetes_str)

    lignes: list[LigneExtraite] = []
    for numero_ligne, valeurs in enumerate(lignes_brutes, start=2):
        if all(v is None for v in valeurs):
            continue

        ligne_brute = dict(zip(entetes_str, valeurs, strict=False))
        resultat = normaliser_ligne(ligne_brute, mapping_colonnes)
        lignes.append(
            LigneExtraite(
                ligne=numero_ligne,
                donnees=resultat.donnees,
                brut={k: valeur_json_safe(v) for k, v in ligne_brute.items() if k},
                erreurs=resultat.erreurs,
            )
        )

    return ResultatExtraction(lignes=lignes)
