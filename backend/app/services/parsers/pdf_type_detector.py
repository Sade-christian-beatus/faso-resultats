"""Détecte si un PDF a une couche texte (natif) ou est un scan (image seule).

Utile car les communiqués de la Fonction publique (`fonction-publique.gov.bf`) sont
systématiquement des scans (HP Scan Extended Application, PaperStream Capture) sans
aucun texte extractible — `pdfplumber` seul ne peut rien en tirer, l'OCR est
obligatoire. Voir `docs/PARSER_PDF_FONCTION_PUBLIQUE.md` § 1.
"""

import subprocess
from pathlib import Path
from typing import Literal

TypePdf = Literal["NATIF", "SCAN"]


def detecter_type_pdf(chemin_fichier: str | Path) -> TypePdf:
    """`pdffonts` (poppler-utils) liste les polices utilisées dans le PDF : une sortie
    de 2 lignes ou moins (juste l'en-tête du tableau, aucune police) signale un PDF
    sans couche texte, donc un scan."""
    resultat = subprocess.run(
        ["pdffonts", str(chemin_fichier)], capture_output=True, text=True, check=True
    )
    lignes = [ligne for ligne in resultat.stdout.strip().split("\n") if ligne.strip()]
    return "SCAN" if len(lignes) <= 2 else "NATIF"
