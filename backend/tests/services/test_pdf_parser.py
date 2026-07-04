from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from app.services.ingestion.normalizer import message_colonnes_non_reconnues
from app.services.ingestion.pdf_parser import parser_pdf


def _construire_pdf_tableau(chemin, entetes: list[str], lignes: list[list]) -> None:
    """Construit un PDF natif avec un tableau à bordures (pdfplumber a besoin de
    lignes visibles pour détecter les cellules ; un Table reportlab sans style
    n'en a pas par défaut)."""
    doc = SimpleDocTemplate(str(chemin), pagesize=A4)
    table = Table([entetes, *lignes], repeatRows=0)
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    doc.build([table])


def test_parser_pdf_extrait_les_lignes_valides(tmp_path) -> None:
    chemin = tmp_path / "resultats.pdf"
    _construire_pdf_tableau(
        chemin,
        ["Numero PV", "Jury", "Nom", "Prenom", "Decision"],
        [
            ["001", "Ouaga 1", "Traore", "Awa", "Admis"],
            ["002", "Ouaga 1", "Kabore", "Issa", "Ajourne"],
        ],
    )

    resultat = parser_pdf(str(chemin))

    assert resultat.nombre_lignes == 2
    assert resultat.nombre_erreurs == 0
    assert resultat.lignes[0].donnees["numero_pv"] == "001"
    assert resultat.lignes[1].donnees["decision"] == "AJOURNE"


def test_parser_pdf_signale_ligne_incomplete(tmp_path) -> None:
    chemin = tmp_path / "resultats.pdf"
    _construire_pdf_tableau(
        chemin,
        ["Numero PV", "Jury", "Nom", "Prenom", "Decision"],
        [["001", "Ouaga 1", "", "Awa", "Admis"]],
    )

    resultat = parser_pdf(str(chemin))

    assert resultat.nombre_erreurs == 1
    assert "nom manquant" in resultat.lignes[0].erreurs


def test_parser_pdf_gere_un_tableau_reparti_sur_plusieurs_pages(tmp_path) -> None:
    """Calibrage sur un vrai document officiel (2026-07-04, liste des
    établissements, 62 pages) : l'en-tête n'apparaît que sur la première page,
    les pages suivantes continuent le tableau directement. Reproduit cette
    structure pour vérifier que le mapping de colonnes (calculé une seule fois)
    reste correct sur les lignes des pages suivantes, sans doublon d'en-tête ni
    perte de ligne."""
    chemin = tmp_path / "resultats_multi_pages.pdf"
    lignes = [[str(n), "Ouaga 1", f"Nom{n}", f"Prenom{n}", "Admis"] for n in range(1, 60)]
    _construire_pdf_tableau(chemin, ["Numero PV", "Jury", "Nom", "Prenom", "Decision"], lignes)

    resultat = parser_pdf(str(chemin))

    assert resultat.nombre_lignes == 59
    assert resultat.nombre_erreurs == 0
    assert resultat.lignes[0].donnees["numero_pv"] == "1"
    assert resultat.lignes[-1].donnees["numero_pv"] == "59"
    assert resultat.lignes[-1].donnees["nom"] == "Nom59"


def test_parser_pdf_document_sans_tableau_signale_erreur_fichier(tmp_path) -> None:
    chemin = tmp_path / "sans_tableau.pdf"
    doc = SimpleDocTemplate(str(chemin), pagesize=A4)
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph

    doc.build([Paragraph("Aucun tableau ici, juste du texte.", getSampleStyleSheet()["Normal"])])

    resultat = parser_pdf(str(chemin))

    assert resultat.lignes == []
    assert resultat.erreurs_fichier == ["Aucun tableau détecté dans le PDF"]


def test_parser_pdf_signale_les_colonnes_non_reconnues(tmp_path) -> None:
    chemin = tmp_path / "resultats.pdf"
    _construire_pdf_tableau(
        chemin,
        ["Numero PV", "Jury", "Nom", "Prenom", "Decision", "Adresse"],
        [["001", "Ouaga 1", "Traore", "Awa", "Admis", "Secteur 15"]],
    )

    resultat = parser_pdf(str(chemin))

    assert resultat.erreurs_fichier == [message_colonnes_non_reconnues(["Adresse"])]


def test_parser_pdf_document_type_incompatible_signale_toutes_les_lignes_en_erreur(
    tmp_path,
) -> None:
    """Un document au mauvais format (ex. une liste d'établissements importée par
    erreur à la place d'un PV de résultats) ne doit jamais être accepté
    silencieusement : ses colonnes ne correspondant à aucun champ métier, chaque
    ligne doit ressortir en erreur et donc bloquer la publication."""
    chemin = tmp_path / "etablissements.pdf"
    _construire_pdf_tableau(
        chemin,
        ["N°", "REGION", "NOM DE L'ETABLISSEMENT", "PROVINCES", "COMMUNES", "SECTEUR/VILLE"],
        [["1", "BOUCLE DU MOUHOUN", "COLLEGE PRIVE X", "BANWA", "SOLENZO", "SOLENZO"]],
    )

    resultat = parser_pdf(str(chemin))

    assert resultat.nombre_lignes == 1
    assert resultat.nombre_erreurs == 1
    assert "numero_pv manquant" in resultat.lignes[0].erreurs
    assert "nom manquant" in resultat.lignes[0].erreurs
