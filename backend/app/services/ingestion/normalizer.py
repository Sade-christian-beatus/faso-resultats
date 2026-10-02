"""Normalisation des lignes brutes extraites d'un fichier source (PDF, Excel, OCR)
vers les champs attendus par le modèle Resultat. Fonctions pures, sans I/O,
pour rester testables sans fichier ni base de données.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Any

CHAMPS_OBLIGATOIRES = ("numero_pv", "nom", "prenom", "jury", "decision")

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


# Row-order columns ("N°", "N° d'ordre") found in nearly every official list: knowingly
# ignored, so they do not raise the file warning that publication asks the admin to
# confirm (a warning raised on every import would end up confirmed without reading).
_COLONNES_ORDRE_IGNOREES = frozenset({"n", "no", "n o", "ordre", "n d ordre", "numero d ordre"})


def colonnes_non_reconnues(
    entetes_brutes: list[str], mapping_colonnes: dict[str, str]
) -> list[str]:
    """En-têtes présentes dans le fichier mais ignorées car aucun champ métier ne leur
    correspond — pour permettre à l'admin de corriger lui-même le nommage de ses colonnes
    plutôt que de nous demander une calibration à chaque nouveau format de document."""
    return [
        entete
        for entete in entetes_brutes
        if entete
        and entete not in mapping_colonnes
        and normaliser_entete(entete) not in _COLONNES_ORDRE_IGNOREES
    ]


def message_colonnes_non_reconnues(non_reconnues: list[str]) -> str:
    return (
        f"Colonnes non reconnues, ignorées : {', '.join(non_reconnues)}. "
        "Si des données y sont attendues, vérifiez le nom de ces colonnes."
    )


def _parser_date(valeur: Any) -> tuple[date | None, str | None]:
    if valeur is None or valeur == "":
        return None, None
    if isinstance(valeur, date):
        return valeur, None
    texte = str(valeur).strip()
    for fmt in _FORMATS_DATE:
        try:
            from datetime import datetime as _dt

            return _dt.strptime(texte, fmt).date(), None
        except ValueError:
            continue
    return None, f"date de naissance illisible : '{texte}'"


def _parser_moyenne(valeur: Any) -> tuple[float | None, str | None]:
    if valeur is None or valeur == "":
        return None, None
    if isinstance(valeur, int | float):
        return float(valeur), None
    texte = str(valeur).strip().replace(",", ".")
    try:
        return float(texte), None
    except ValueError:
        return None, f"moyenne illisible : '{texte}'"


def valider_ligne_normalisee(donnees: dict[str, Any]) -> list[str]:
    """Revalide une ligne déjà en forme canonique (ex. après correction manuelle par un
    admin), en rejouant les mêmes règles que `normaliser_ligne` sur les champs
    individuels. Contrairement à `normaliser_ligne`, ne fait aucun mapping d'en-têtes :
    suppose que les clés de `donnees` sont déjà les champs canoniques (numero_pv, jury,
    nom, ...). Sert de garde-fou serveur : on ne peut jamais faire confiance à la liste
    `erreurs` telle qu'envoyée par le client (validation humaine obligatoire = revalidée
    côté serveur, pas seulement affichée côté client).
    """
    erreurs: list[str] = []
    for champ in CHAMPS_OBLIGATOIRES:
        if not donnees.get(champ):
            erreurs.append(f"{champ} manquant")

    date_naissance = donnees.get("date_naissance")
    if date_naissance:
        try:
            date.fromisoformat(str(date_naissance))
        except ValueError:
            erreurs.append(f"date de naissance illisible : '{date_naissance}'")

    moyenne = donnees.get("moyenne")
    if moyenne is not None and not isinstance(moyenne, int | float):
        try:
            float(str(moyenne).replace(",", "."))
        except ValueError:
            erreurs.append(f"moyenne illisible : '{moyenne}'")

    return erreurs


@dataclass
class ResultatNormalisation:
    donnees: dict[str, Any]
    erreurs: list[str] = field(default_factory=list)


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

    if not valeurs.get("decision") and decision_par_defaut:
        valeurs["decision"] = decision_par_defaut

    erreurs: list[str] = []

    for champ in CHAMPS_OBLIGATOIRES:
        if not valeurs.get(champ):
            erreurs.append(f"{champ} manquant")

    date_naissance, erreur_date = _parser_date(valeurs.get("date_naissance"))
    if erreur_date:
        erreurs.append(erreur_date)

    moyenne, erreur_moyenne = _parser_moyenne(valeurs.get("moyenne"))
    if erreur_moyenne:
        erreurs.append(erreur_moyenne)

    donnees = {
        "numero_pv": str(valeurs.get("numero_pv") or "").strip(),
        "jury": str(valeurs.get("jury") or "").strip(),
        "nom": str(valeurs.get("nom") or "").strip(),
        "prenom": str(valeurs.get("prenom") or "").strip(),
        "decision": str(valeurs.get("decision") or "").strip().upper(),
        "date_naissance": date_naissance.isoformat() if date_naissance else None,
        "lieu_naissance": str(valeurs.get("lieu_naissance") or "").strip() or None,
        "etablissement": str(valeurs.get("etablissement") or "").strip() or None,
        "numero_cnib": str(valeurs.get("numero_cnib") or "").strip() or None,
        "moyenne": moyenne,
    }

    return ResultatNormalisation(donnees=donnees, erreurs=erreurs)
