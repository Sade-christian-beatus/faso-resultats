"""Parser des communiqués PDF scannés de la Fonction publique (concours directs).

Adapté de `docs/parser_poc.py` (validé à 100% sur 2 PDF officiels 2025 : 7/7 et
120/120 résultats extraits) pour s'intégrer au pipeline d'ingestion existant :
- Réutilise `pdf2image` + `pytesseract` (déjà utilisés par `ocr_parser.py`) plutôt que
  les appels `subprocess` bruts à `pdftoppm`/`tesseract` du POC.
- `--psm 6` (comme le POC) : mode bloc de texte uniforme, nécessaire pour préserver
  l'ordre naturel des lignes (voir calibrage OCR du 2026-07-04 dans ARCHITECTURE.md).
- Produit des `LigneExtraite`/`ResultatExtraction` (types communs du pipeline
  d'ingestion) au lieu des dataclasses `MetadonneesPdf`/`Resultat` du POC, pour
  passer par le même flux upload → aperçu → correction → publication que les autres
  parsers, sans duplication de mécanisme.

Format cible, voir `docs/PARSER_PDF_FONCTION_PUBLIQUE.md` § 2 :
"1° KONATE BEN OUMAR STANISLAS KONABE 000015-120-03 B18622704 03/12/97"
RANG | NOM ET PRÉNOM(s) | RECEPISSE-CODE-CENTRE | N°CNIB | DATE NAISS.
"""

import re
from datetime import date
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

from app.services.ingestion.types import LigneExtraite, ResultatExtraction

CHAMPS_OBLIGATOIRES = ("numero_pv", "nom", "prenom", "jury", "decision")

# Le rang peut avoir 1 à 3 chiffres, suivi de ° (parfois lu O/o par l'OCR).
_RE_LIGNE_RESULTAT = re.compile(
    r"^\s*(\d{1,3})\s*[°oO]\s+"  # rang (1°)
    r"(.+?)\s+"  # nom complet (lazy)
    r"(\d{6})-(\d{2,4})-(\d{2})\s+"  # récépissé-code concours-code centre
    r"([A-Z]?\d{6,10})\s+"  # CNIB (peut commencer par une lettre)
    r"(\d{2}[/\-]\d{2}[/\-]\d{2,4})\s*$"  # date de naissance
)

_RE_NOMBRE_DECLARE = re.compile(
    r"Arr[êe]t[ée]\s+la\s+pr[ée]sente\s+liste\s+[àa]\s+(\d+)\s+(?:admissibles?|admis)",
    re.IGNORECASE,
)

_RE_DECISION = re.compile(r"\bADMISSIBLES?\b|\bADMIS\b", re.IGNORECASE)


def _pretraiter_image(image_pil) -> np.ndarray:
    image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2GRAY)
    return cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
    )


def _extraire_texte(chemin_fichier: str | Path) -> str:
    pages = convert_from_path(str(chemin_fichier))
    textes = [
        pytesseract.image_to_string(_pretraiter_image(page), lang="fra", config="--psm 6")
        for page in pages
    ]
    return "\n".join(textes)


def _normaliser_date_naissance(texte_date: str) -> str | None:
    """'03/12/97' -> '1997-12-03'. Suppose 20xx si année à 2 chiffres < 30, sinon 19xx."""
    parts = re.split(r"[/\-]", texte_date)
    if len(parts) != 3:
        return None
    jour, mois, annee = parts
    if len(annee) == 2:
        annee = f"20{annee}" if int(annee) < 30 else f"19{annee}"
    try:
        return date(int(annee), int(mois), int(jour)).isoformat()
    except ValueError:
        return None


def _detecter_decision(texte: str, decision_par_defaut: str | None) -> str | None:
    """Le communiqué déclare la phase dans son titre ("ADMISSIBLES", "ADMIS") — elle
    s'applique à toutes les lignes du document, comme `decision_par_defaut` pour les
    autres parsers, mais détectée automatiquement plutôt que saisie par l'admin."""
    trouve = _RE_DECISION.search(texte)
    if trouve:
        return "ADMISSIBLE" if "ADMISSIBLE" in trouve.group(0).upper() else "ADMIS"
    return decision_par_defaut


def parser_pdf_scan(
    chemin_fichier: str | Path, decision_par_defaut: str | None = None
) -> ResultatExtraction:
    """Extrait les résultats d'un communiqué PDF scanné de la Fonction publique."""
    texte = _extraire_texte(chemin_fichier)
    decision = _detecter_decision(texte, decision_par_defaut)

    lignes: list[LigneExtraite] = []
    numero_ligne = 1
    for ligne_brute in texte.split("\n"):
        ligne_nettoyee = ligne_brute.strip()
        correspondance = _RE_LIGNE_RESULTAT.match(ligne_nettoyee)
        if not correspondance:
            continue
        numero_ligne += 1

        rang_numerique = int(correspondance.group(1))
        numero_recepisse = correspondance.group(3)

        donnees = {
            "numero_pv": numero_recepisse,
            "numero_recepisse": numero_recepisse,
            "jury": correspondance.group(5),
            "code_centre": correspondance.group(5),
            "code_concours": correspondance.group(4),
            "rang_numerique": rang_numerique,
            "rang_affiche": f"{rang_numerique}°",
            "nom": correspondance.group(2).strip(),
            "prenom": "",
            "decision": decision or "",
            "numero_cnib": correspondance.group(6),
            "date_naissance": _normaliser_date_naissance(correspondance.group(7)),
            "lieu_naissance": None,
            "etablissement": None,
            "moyenne": None,
        }
        erreurs = [f"{champ} manquant" for champ in CHAMPS_OBLIGATOIRES if not donnees.get(champ)]

        lignes.append(
            LigneExtraite(
                ligne=numero_ligne,
                donnees=donnees,
                brut={"ligne_ocr": ligne_nettoyee},
                erreurs=erreurs,
            )
        )

    erreurs_fichier: list[str] = []
    if not lignes:
        erreurs_fichier.append("Aucune ligne de résultat reconnue dans ce PDF scanné")
    else:
        nombre_declare = _RE_NOMBRE_DECLARE.search(texte)
        if nombre_declare and int(nombre_declare.group(1)) != len(lignes):
            erreurs_fichier.append(
                f"Écart détecté : {len(lignes)} ligne(s) extraite(s) contre "
                f"{nombre_declare.group(1)} annoncée(s) en pied de document. "
                "Vérifiez le document ou les lignes non reconnues."
            )

    return ResultatExtraction(lignes=lignes, erreurs_fichier=erreurs_fichier)
