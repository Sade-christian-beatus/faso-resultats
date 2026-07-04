"""
POC de parser pour les PDF de résultats de concours directs
de la Fonction Publique burkinabè.

Ces PDF sont des SCANS (pas de layer texte), donc OCR obligatoire.
Format observé stable sur les publications 2025 :
- En-tête administratif standard
- Titre du concours + phase (ADMISSIBLES)
- Tableau : RANG | NOM ET PRÉNOM | RÉCÉPISSÉ-CODE-CENTRE + N°CNIB | DATE NAISS.
- Pied : "Arrêté la présente liste à X admissible(s)"
"""

import re
import subprocess
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import tempfile


@dataclass
class MetadonneesPdf:
    """En-tête du communiqué officiel."""
    numero_communique: str | None = None       # ex: "25-00782/MFPTPS/SG/AGRE/DOC"
    date_communique: str | None = None          # ex: "22 JUIL 2025"
    ministere: str | None = None                # "Fonction Publique"
    corps_concours: str | None = None           # "CHIRURGIENS-DENTISTES GÉNÉRALISTES"
    session: str | None = None                  # "2025"
    nombre_places: int | None = None            # 10 (déclaré)
    phase: str = "ADMISSIBILITE"                # ADMISSIBILITE / ADMISSION_DEFINITIVE
    code_concours: str | None = None            # extrait des lignes ("120" pour dentistes)


@dataclass
class Resultat:
    """Une ligne du tableau des admissibles."""
    rang: int                       # 1, 2, 4 (ex-aequo) etc.
    rang_affiche: str               # "1°", "4°", "16°" — pour affichage utilisateur
    nom_complet: str                # "KONATE BEN OUMAR STANISLAS KONABE"
    numero_recepisse: str           # "000015" — c'est le PV du candidat
    code_concours: str              # "120"
    code_centre: str                # "03"
    numero_cnib: str                # "B18622704"
    date_naissance: str             # "03/12/97" (à normaliser JJ/MM/AAAA)


@dataclass
class ResultatIngestion:
    metadonnees: MetadonneesPdf
    resultats: list[Resultat] = field(default_factory=list)
    nombre_admissibles_declare: int | None = None
    lignes_non_parsees: list[str] = field(default_factory=list)  # pour audit


def rasteriser_et_ocr(pdf_path: str, dpi: int = 200) -> str:
    """Rasterise chaque page et applique Tesseract en français.

    Retourne le texte OCR concaténé de toutes les pages.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Rasteriser toutes les pages
        subprocess.run(
            ["pdftoppm", "-jpeg", "-r", str(dpi), pdf_path, f"{tmpdir}/page"],
            check=True, capture_output=True,
        )
        # OCR de chaque page
        pages = sorted(Path(tmpdir).glob("page-*.jpg"))
        texte_total = []
        for page in pages:
            result = subprocess.run(
                ["tesseract", str(page), "-", "-l", "fra", "--psm", "6"],
                check=True, capture_output=True, text=True,
            )
            texte_total.append(result.stdout)
        return "\n".join(texte_total)


# --- Regex de parsing ---

# Ligne de résultat type :
# "1° KONATE BEN OUMAR STANISLAS KONABE 000015-120-03 B18622704 03/12/97"
# Le rang peut avoir 1 à 3 chiffres, suivi de ° (parfois O ou o si l'OCR se trompe)
RE_LIGNE_RESULTAT = re.compile(
    r"^\s*(\d{1,3})\s*[°oO]\s+"                    # rang (1°)
    r"(.+?)\s+"                                     # nom complet (lazy)
    r"(\d{6})-(\d{2,4})-(\d{2})\s+"                 # récépissé-code-centre
    r"([A-Z]?\d{6,10})\s+"                          # CNIB (peut commencer par A/B)
    r"(\d{2}[/\-]\d{2}[/\-]\d{2,4})\s*$"            # date de naissance
)

RE_NB_ADMISSIBLES = re.compile(
    r"Arrêté\s+la\s+présente\s+liste\s+à\s+(\d+)\s+admissible", re.IGNORECASE
)

RE_NUMERO_COMMUNIQUE = re.compile(
    r"N[°ºo]?\s*(\d{2}-\d{4,5})[/\s]*(MFPTPS|MFPTSS)?"
)

RE_NB_PLACES = re.compile(
    r"recrutement\s+de\s+\w+\s+\((\d+)\)", re.IGNORECASE
)

RE_TITRE_CORPS = re.compile(
    r"^\s*([A-ZÉÈÊÀÂÎÏÔÙÜÇ][A-ZÉÈÊÀÂÎÏÔÙÜÇ\s\-/]{10,})\s*$"
)


def normaliser_date(date_str: str) -> str:
    """Convertit '03/12/97' → '03/12/1997'. Suppose 20xx si année < 30."""
    parts = re.split(r"[/\-]", date_str)
    if len(parts) != 3:
        return date_str
    jour, mois, annee = parts
    if len(annee) == 2:
        annee = f"20{annee}" if int(annee) < 30 else f"19{annee}"
    return f"{jour}/{mois}/{annee}"


def parser_texte_ocr(texte: str) -> ResultatIngestion:
    """Parse le texte OCR complet et retourne une structure exploitable."""
    metadata = MetadonneesPdf()
    resultats: list[Resultat] = []
    lignes_non_parsees: list[str] = []
    nb_admissibles = None
    code_concours_frequent = {}  # pour identifier le code du concours

    lignes = texte.split("\n")

    for ligne in lignes:
        ligne_clean = ligne.strip()

        if not ligne_clean:
            continue

        # Résultat individuel
        m = RE_LIGNE_RESULTAT.match(ligne_clean)
        if m:
            rang_num = int(m.group(1))
            nom = m.group(2).strip()
            recepisse = m.group(3)
            code_conc = m.group(4)
            code_centre = m.group(5)
            cnib = m.group(6)
            date_naiss = normaliser_date(m.group(7))

            resultats.append(Resultat(
                rang=rang_num,
                rang_affiche=f"{rang_num}°",
                nom_complet=nom,
                numero_recepisse=recepisse,
                code_concours=code_conc,
                code_centre=code_centre,
                numero_cnib=cnib,
                date_naissance=date_naiss,
            ))
            code_concours_frequent[code_conc] = code_concours_frequent.get(code_conc, 0) + 1
            continue

        # Métadonnées
        if not metadata.numero_communique:
            m = RE_NUMERO_COMMUNIQUE.search(ligne_clean)
            if m:
                metadata.numero_communique = f"{m.group(1)}/{m.group(2) or 'MFPTPS'}/SG/AGRE/DOC"

        if not metadata.nombre_places:
            m = RE_NB_PLACES.search(ligne_clean)
            if m:
                metadata.nombre_places = int(m.group(1))

        m = RE_NB_ADMISSIBLES.search(ligne_clean)
        if m:
            nb_admissibles = int(m.group(1))

        # Si la ligne ne matche aucun pattern connu et ressemble à du contenu utile,
        # on la garde pour audit
        if len(ligne_clean) > 5 and not ligne_clean.startswith(("|", "\\", "/", "@")):
            if not any([
                m,
                "MINISTERE" in ligne_clean.upper(),
                "BURKINA" in ligne_clean.upper(),
                "SECRETARIAT" in ligne_clean.upper(),
                "AGENCE" in ligne_clean.upper(),
                "DIRECTION" in ligne_clean.upper(),
                "COMMUNIQUE" in ligne_clean.upper(),
                "Sous réserve" in ligne_clean,
                "candidats" in ligne_clean.lower(),
                "RANG" in ligne_clean.upper(),
                "ADMISSIBLES" in ligne_clean.upper(),
                "Arrêté" in ligne_clean,
                "Par ailleurs" in ligne_clean,
                "compter" in ligne_clean,
                "déposer" in ligne_clean,
                "Ministre" in ligne_clean,
                "Ordre" in ligne_clean,
                "Chevalier" in ligne_clean,
            ]):
                lignes_non_parsees.append(ligne_clean)

    # Déduire le code concours dominant
    if code_concours_frequent:
        metadata.code_concours = max(code_concours_frequent, key=code_concours_frequent.get)

    return ResultatIngestion(
        metadonnees=metadata,
        resultats=resultats,
        nombre_admissibles_declare=nb_admissibles,
        lignes_non_parsees=lignes_non_parsees,
    )


def analyser_pdf(pdf_path: str) -> dict:
    """Pipeline complet : PDF → OCR → parsing → validation."""
    print(f"\n{'='*70}")
    print(f"ANALYSE : {Path(pdf_path).name}")
    print(f"{'='*70}")

    texte = rasteriser_et_ocr(pdf_path)
    ingestion = parser_texte_ocr(texte)

    # Validation
    nb_extrait = len(ingestion.resultats)
    nb_declare = ingestion.nombre_admissibles_declare
    coherence = (nb_extrait == nb_declare) if nb_declare else None

    resultat = {
        "fichier": Path(pdf_path).name,
        "metadonnees": asdict(ingestion.metadonnees),
        "nombre_resultats_extraits": nb_extrait,
        "nombre_admissibles_declare": nb_declare,
        "coherence_totaux": coherence,
        "premiers_resultats": [asdict(r) for r in ingestion.resultats[:5]],
        "derniers_resultats": [asdict(r) for r in ingestion.resultats[-3:]] if nb_extrait > 5 else [],
        "lignes_non_parsees_significatives": ingestion.lignes_non_parsees[:10],
    }

    print(f"Métadonnées : {ingestion.metadonnees}")
    print(f"Résultats extraits : {nb_extrait}")
    print(f"Admissibles déclarés : {nb_declare}")
    print(f"Cohérence : {'✅ OK' if coherence else '⚠️ Écart'}")
    print(f"Premiers résultats :")
    for r in ingestion.resultats[:3]:
        print(f"  {r.rang_affiche} {r.nom_complet:40s} PV:{r.numero_recepisse} CNIB:{r.numero_cnib} Né(e):{r.date_naissance}")

    return resultat


if __name__ == "__main__":
    fichiers = [
        "/mnt/user-data/uploads/0000_Resultat_cd_2025_chirurgiens-dentistes_generalistes.pdf",
        "/mnt/user-data/uploads/YYY_U9-RESULTAT_CD_2025_INGENIEURS_EN_GENIE_BIOMEDICAL.pdf",
    ]

    rapports = [analyser_pdf(f) for f in fichiers]

    # Sauvegarde JSON pour inspection
    with open("/home/claude/pdf_analysis/rapport_parsing.json", "w", encoding="utf-8") as f:
        json.dump(rapports, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print("SYNTHÈSE")
    print(f"{'='*70}")
    for r in rapports:
        status = "✅" if r["coherence_totaux"] else "⚠️"
        print(f"{status} {r['fichier']}: {r['nombre_resultats_extraits']}/{r['nombre_admissibles_declare']} résultats")
