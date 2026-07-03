"""Parsing des PV scannés (image) via OCR.

Contrairement aux parsers PDF natif / Excel, la qualité d'extraction dépend
fortement de la mise en page du document scanné. La logique est donc séparée
en deux temps :
- `extraire_texte_ocr` : pipeline image (pdf2image + OpenCV + pytesseract),
  nécessite les binaires tesseract/poppler (installés dans le Dockerfile).
- `lignes_depuis_texte` : découpage du texte brut en lignes/colonnes, fonction
  pure testable sans dépendance externe.

⚠️ Cette heuristique (colonnes séparées par ≥2 espaces) est un premier jet :
elle doit être calibrée sur de vrais PV scannés OCECOS/DGEC dès qu'ils seront
disponibles.
"""

import re
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

from app.services.ingestion.normalizer import construire_mapping_colonnes, normaliser_ligne
from app.services.ingestion.types import LigneExtraite, ResultatExtraction

_SEPARATEUR_COLONNES = re.compile(r"\s{2,}")


def _pretraiter_image(image_pil) -> np.ndarray:
    image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2GRAY)
    return cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )


def extraire_texte_ocr(chemin_fichier: str | Path) -> str:
    pages = convert_from_path(str(chemin_fichier))
    textes = [pytesseract.image_to_string(_pretraiter_image(page), lang="fra") for page in pages]
    return "\n".join(textes)


def lignes_depuis_texte(texte: str) -> ResultatExtraction:
    lignes_texte = [ligne for ligne in texte.splitlines() if ligne.strip()]
    if not lignes_texte:
        return ResultatExtraction(lignes=[], erreurs_fichier=["Aucun texte détecté par l'OCR"])

    entetes = _SEPARATEUR_COLONNES.split(lignes_texte[0].strip())
    mapping_colonnes = construire_mapping_colonnes(entetes)

    lignes: list[LigneExtraite] = []
    for numero_ligne, ligne_texte in enumerate(lignes_texte[1:], start=2):
        valeurs = _SEPARATEUR_COLONNES.split(ligne_texte.strip())
        ligne_brute = dict(zip(entetes, valeurs, strict=False))
        resultat = normaliser_ligne(ligne_brute, mapping_colonnes)
        lignes.append(
            LigneExtraite(
                ligne=numero_ligne,
                donnees=resultat.donnees,
                brut={k: v for k, v in ligne_brute.items() if k},
                erreurs=resultat.erreurs,
            )
        )

    return ResultatExtraction(lignes=lignes)


def parser_ocr(chemin_fichier: str | Path) -> ResultatExtraction:
    texte = extraire_texte_ocr(chemin_fichier)
    return lignes_depuis_texte(texte)
