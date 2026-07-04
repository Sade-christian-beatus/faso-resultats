"""Génère le modèle Excel téléchargeable depuis l'admin, avec les en-têtes exactes
reconnues par le parser — pour qu'une administration qui n'a pas encore de fichier
dans un format compatible parte d'un modèle garanti fiable, sans attendre une
calibration de notre part sur son propre document source.
"""

import io

import openpyxl
from openpyxl.styles import Font

_ENTETES_MODELE = (
    "Numéro PV",
    "Jury",
    "Nom",
    "Prénom",
    "Date de naissance",
    "Décision",
    "Moyenne",
    "Établissement",
    "N°CNIB",
)

_LIGNE_EXEMPLE = (
    "001",
    "Ouaga 1",
    "Traore",
    "Awa",
    "12/05/2008",
    "Admis",
    13.45,
    "Lycée Philippe Zinda Kaboré",
    "",
)


def construire_modele_excel() -> bytes:
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.title = "Résultats"
    feuille.append(_ENTETES_MODELE)
    for cellule in feuille[1]:
        cellule.font = Font(bold=True)
    feuille.append(_LIGNE_EXEMPLE)

    buffer = io.BytesIO()
    classeur.save(buffer)
    return buffer.getvalue()
