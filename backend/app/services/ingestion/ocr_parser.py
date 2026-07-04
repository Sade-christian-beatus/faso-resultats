"""Parsing des PV scannés (image) via OCR.

Contrairement aux parsers PDF natif / Excel, la qualité d'extraction dépend
fortement de la mise en page du document scanné. La logique est donc séparée
en deux temps :
- `extraire_texte_ocr` : pipeline image (pdf2image + OpenCV + pytesseract),
  nécessite les binaires tesseract/poppler (installés dans le Dockerfile).
- `lignes_depuis_texte` : découpage du texte brut en lignes/colonnes, fonction
  pure testable sans dépendance externe.

Calibré le 2026-07-04 sur une reconstitution fidèle d'un vrai PV scanné
(Assistants des Douanes) — voir `docs/ARCHITECTURE.md` § Calibrage OCR :
- `--psm 6` est indispensable : le mode par défaut de Tesseract (segmentation
  automatique de page) regroupe le texte par bloc/colonne détecté plutôt que
  ligne par ligne sur un tableau large, ce qui mélangeait entièrement les
  colonnes (tous les N°, puis tous les noms, puis tous les récépissés...).
- L'en-tête du tableau n'est pas forcément la première ligne de texte : les
  documents officiels ont presque toujours un titre au-dessus ("ASSISTANTS
  DES DOUANES/HOMMES", "ADMISSIBLES") — `_trouver_ligne_entete` cherche la
  première ligne qui reconnaît au moins 2 colonnes métier plutôt que de
  supposer que c'est la ligne 1.

⚠️ Calibré sur un seul document reconstitué : l'heuristique (colonnes
séparées par ≥2 espaces) reste un premier jet à confirmer sur un vrai PV
scanné/photographié (fichier original, pas une reconstitution).
"""

import re
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

from app.services.ingestion.normalizer import (
    colonnes_non_reconnues,
    construire_mapping_colonnes,
    message_colonnes_non_reconnues,
    normaliser_ligne,
)
from app.services.ingestion.types import LigneExtraite, ResultatExtraction

_SEPARATEUR_COLONNES = re.compile(r"\s{2,}")
_MINIMUM_COLONNES_RECONNUES = 2


def _pretraiter_image(image_pil) -> np.ndarray:
    image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2GRAY)
    return cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )


def extraire_texte_ocr(chemin_fichier: str | Path) -> str:
    pages = convert_from_path(str(chemin_fichier))
    textes = [
        pytesseract.image_to_string(_pretraiter_image(page), lang="fra", config="--psm 6")
        for page in pages
    ]
    return "\n".join(textes)


def _trouver_ligne_entete(lignes_texte: list[str]) -> int:
    """Cherche la première ligne qui reconnaît au moins 2 colonnes métier, pour ignorer
    les titres/sous-titres qui précèdent presque toujours l'en-tête sur les documents
    officiels (ex. "ASSISTANTS DES DOUANES/HOMMES", "ADMISSIBLES")."""
    for index, ligne in enumerate(lignes_texte):
        candidats = _SEPARATEUR_COLONNES.split(ligne.strip())
        if len(construire_mapping_colonnes(candidats)) >= _MINIMUM_COLONNES_RECONNUES:
            return index
    return 0


def lignes_depuis_texte(texte: str, decision_par_defaut: str | None = None) -> ResultatExtraction:
    lignes_texte = [ligne for ligne in texte.splitlines() if ligne.strip()]
    if not lignes_texte:
        return ResultatExtraction(lignes=[], erreurs_fichier=["Aucun texte détecté par l'OCR"])

    index_entete = _trouver_ligne_entete(lignes_texte)
    entetes = _SEPARATEUR_COLONNES.split(lignes_texte[index_entete].strip())
    mapping_colonnes = construire_mapping_colonnes(entetes)

    lignes: list[LigneExtraite] = []
    for numero_ligne, ligne_texte in enumerate(lignes_texte[index_entete + 1 :], start=2):
        valeurs = _SEPARATEUR_COLONNES.split(ligne_texte.strip())
        ligne_brute = dict(zip(entetes, valeurs, strict=False))
        resultat = normaliser_ligne(ligne_brute, mapping_colonnes, decision_par_defaut)
        lignes.append(
            LigneExtraite(
                ligne=numero_ligne,
                donnees=resultat.donnees,
                brut={k: v for k, v in ligne_brute.items() if k},
                erreurs=resultat.erreurs,
            )
        )

    non_reconnues = colonnes_non_reconnues(entetes, mapping_colonnes)
    erreurs_fichier = [message_colonnes_non_reconnues(non_reconnues)] if non_reconnues else []
    return ResultatExtraction(lignes=lignes, erreurs_fichier=erreurs_fichier)


def parser_ocr(
    chemin_fichier: str | Path, decision_par_defaut: str | None = None
) -> ResultatExtraction:
    texte = extraire_texte_ocr(chemin_fichier)
    return lignes_depuis_texte(texte, decision_par_defaut)
