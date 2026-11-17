"""Normalisation des lignes brutes extraites d'un fichier source (PDF, Excel, OCR)
vers les champs attendus par le modèle Resultat. Fonctions pures, sans I/O,
pour rester testables sans fichier ni base de données.
"""

import math
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

CHAMPS_OBLIGATOIRES = ("numero_pv", "nom", "prenom", "jury", "decision")
_CHAMPS_TEXTE_OPTIONNELS = ("lieu_naissance", "etablissement", "numero_cnib")

# Minimum number of distinct business columns recognised in a table row for it to be a
# repeated header rather than a candidate (see `est_ligne_entete`).
_MINIMUM_COLONNES_ENTETE = 2

# Alias d'en-têtes tolérés par champ canonique (déjà normalisés : minuscules, sans accent).
_ALIAS_ENTETES: dict[str, tuple[str, ...]] = {
    "numero_pv": (
        "numero_pv",
        "numero pv",
        "num pv",
        "n pv",
        "matricule",
        "recepisse code centre",
        "recepisse",
    ),
    "jury": ("jury", "centre", "centre d examen", "centre examen"),
    "nom": ("nom",),
    "prenom": ("prenom", "prenoms"),
    # Documents de concours direct : une seule colonne nom+prénom combinés. Pas de
    # découpage automatique (risque d'erreur sur les noms composés) — le nom complet
    # est importé tel quel dans "nom", ce qui laisse "prenom" vide et donc signalé en
    # erreur, pour que l'admin le sépare manuellement dans l'écran de correction.
    "nom_prenom": ("nom et prenom", "nom et prenom s", "nom et prenoms", "noms et prenoms"),
    "date_naissance": ("date de naissance", "date_naissance", "date nais", "ne le", "nee le"),
    "lieu_naissance": ("lieu de naissance", "lieu_naissance"),
    "etablissement": ("etablissement", "ecole"),
    "decision": ("decision", "resultat", "mention"),
    "moyenne": ("moyenne", "moy"),
    "numero_cnib": ("n cnib", "cnib", "numero cnib"),
}

# Années à 2 chiffres en fin de liste (moins prioritaires) : format courant sur les
# documents de concours (ex. "15/02/01"), calibré sur un vrai PV OCECOS/AGRE.
_FORMATS_DATE = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y")


def _sans_accents(texte: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn"
    )


def normaliser_entete(entete: str) -> str:
    """'Numéro PV' -> 'numero pv' ; 'Prénom(s)' -> 'prenom s' etc."""
    texte = _sans_accents(str(entete)).lower().strip()
    texte = re.sub(r"[^a-z0-9]+", " ", texte).strip()
    return texte


def construire_mapping_colonnes(entetes_brutes: list[str]) -> dict[str, str]:
    """Associe chaque en-tête brute du fichier au champ canonique correspondant, si reconnu."""
    mapping: dict[str, str] = {}
    for entete_brute in entetes_brutes:
        entete_normalisee = normaliser_entete(entete_brute)
        for champ, alias in _ALIAS_ENTETES.items():
            if entete_normalisee in alias:
                mapping[entete_brute] = champ
                break
    return mapping


def colonnes_non_reconnues(
    entetes_brutes: list[str], mapping_colonnes: dict[str, str]
) -> list[str]:
    """En-têtes présentes dans le fichier mais ignorées car aucun champ métier ne leur
    correspond — pour permettre à l'admin de corriger lui-même le nommage de ses colonnes
    plutôt que de nous demander une calibration à chaque nouveau format de document."""
    return [entete for entete in entetes_brutes if entete and entete not in mapping_colonnes]


def message_colonnes_non_reconnues(non_reconnues: list[str]) -> str:
    return (
        f"Colonnes non reconnues, ignorées : {', '.join(non_reconnues)}. "
        "Si des données y sont attendues, vérifiez le nom de ces colonnes."
    )


def est_ligne_entete(valeurs: list[Any]) -> bool:
    """True when a table row is the column header again rather than a candidate.
    Official PDFs usually repeat the header at the top of every page; without this check
    each repetition was imported as a candidate named "Nom" with decision "DECISION",
    without any error (audit 2026-11-16, C2). Two distinct recognised business columns
    are required: a real candidate row never has two cells that are header names."""
    cellules = [str(v) for v in valeurs if v is not None and str(v).strip()]
    champs = set(construire_mapping_colonnes(cellules).values())
    return len(champs) >= _MINIMUM_COLONNES_ENTETE


def _parser_date(valeur: Any) -> tuple[date | None, str | None]:
    if valeur is None or valeur == "":
        return None, None
    # Checked before `date`: datetime is a subclass of date, and openpyxl returns date
    # cells as datetime — kept as is, isoformat() then carried a time ("2008-05-12T00:00:00")
    # that made publication fail (audit 2026-11-16, C1).
    if isinstance(valeur, datetime):
        return valeur.date(), None
    if isinstance(valeur, date):
        return valeur, None
    texte = str(valeur).strip()
    for fmt in _FORMATS_DATE:
        try:
            return datetime.strptime(texte, fmt).date(), None
        except ValueError:
            continue
    try:
        # ISO date or datetime, e.g. a preview stored before the fix above.
        return datetime.fromisoformat(texte).date(), None
    except ValueError:
        return None, f"date de naissance illisible : '{texte}'"


def _parser_moyenne(valeur: Any) -> tuple[float | None, str | None]:
    if valeur is None or valeur == "":
        return None, None
    if isinstance(valeur, bool):
        return None, f"moyenne illisible : '{valeur}'"
    if isinstance(valeur, int | float):
        nombre: float = float(valeur)
    else:
        texte = str(valeur).strip().replace(",", ".")
        try:
            nombre = float(texte)
        except ValueError:
            return None, f"moyenne illisible : '{texte}'"
    if not math.isfinite(nombre):  # "nan", "inf" parse as floats
        return None, f"moyenne illisible : '{valeur}'"
    return nombre, None


def _texte(valeur: Any) -> str:
    return "" if valeur is None else str(valeur).strip()


@dataclass
class ResultatNormalisation:
    donnees: dict[str, Any]
    erreurs: list[str] = field(default_factory=list)


def normaliser_donnees(donnees: dict[str, Any]) -> ResultatNormalisation:
    """Canonical form and validation of a row already keyed by canonical fields
    (numero_pv, jury, nom...). Single source of truth used at import, after a manual
    correction and again at publication, so that what is validated is exactly what gets
    published — the client's `erreurs` list and value formats are never trusted
    (audit 2026-08-17 and 2026-11-16, E5).

    Fields this function does not know (numero_recepisse, rang... from the scanned-PDF
    parser) are kept unchanged. An unreadable date or average is kept as typed, with its
    error, so that the error stays visible until someone fixes the value instead of the
    value silently disappearing."""
    normalisees = dict(donnees)
    for champ in ("numero_pv", "jury", "nom", "prenom"):
        normalisees[champ] = _texte(donnees.get(champ))
    normalisees["decision"] = _texte(donnees.get("decision")).upper()
    for champ in _CHAMPS_TEXTE_OPTIONNELS:
        normalisees[champ] = _texte(donnees.get(champ)) or None

    erreurs = [f"{champ} manquant" for champ in CHAMPS_OBLIGATOIRES if not normalisees[champ]]

    date_naissance, erreur_date = _parser_date(donnees.get("date_naissance"))
    if erreur_date:
        erreurs.append(erreur_date)
        normalisees["date_naissance"] = _texte(donnees.get("date_naissance"))
    else:
        normalisees["date_naissance"] = date_naissance.isoformat() if date_naissance else None

    moyenne, erreur_moyenne = _parser_moyenne(donnees.get("moyenne"))
    if erreur_moyenne:
        erreurs.append(erreur_moyenne)
        normalisees["moyenne"] = _texte(donnees.get("moyenne"))
    else:
        normalisees["moyenne"] = moyenne

    return ResultatNormalisation(donnees=normalisees, erreurs=erreurs)


def normaliser_ligne(
    ligne_brute: dict[str, Any],
    mapping_colonnes: dict[str, str],
    decision_par_defaut: str | None = None,
) -> ResultatNormalisation:
    """Transforme une ligne brute (en-têtes du fichier -> valeurs) en champs canoniques
    prêts pour Resultat, en collectant les erreurs de validation plutôt qu'en levant une
    exception : chaque ligne en erreur reste visible pour correction manuelle.

    `decision_par_defaut` : pour les fichiers sans colonne décision par ligne (ex. une
    liste d'admissibilité à un concours, où la décision vaut pour tout le document) —
    appliqué uniquement si la ligne n'a pas déjà sa propre décision.
    """
    valeurs: dict[str, Any] = {}
    for entete_brute, valeur in ligne_brute.items():
        champ = mapping_colonnes.get(entete_brute)
        if champ:
            valeurs[champ] = valeur.strip() if isinstance(valeur, str) else valeur

    if not valeurs.get("nom") and valeurs.get("nom_prenom"):
        valeurs["nom"] = valeurs["nom_prenom"]
    valeurs.pop("nom_prenom", None)

    if not valeurs.get("decision") and decision_par_defaut:
        valeurs["decision"] = decision_par_defaut

    return normaliser_donnees(valeurs)
