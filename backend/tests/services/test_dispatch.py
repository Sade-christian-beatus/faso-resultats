from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from app.models import TypeFichier
from app.services.ingestion.dispatch import parser_fichier

_FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)


def test_parser_fichier_pdf_natif_route_vers_le_parser_de_tableau(tmp_path) -> None:
    chemin = tmp_path / "natif.pdf"
    doc = SimpleDocTemplate(str(chemin), pagesize=A4)
    table = Table(
        [
            ["Numero PV", "Jury", "Nom", "Prenom", "Decision"],
            ["001", "Ouaga 1", "Traore", "Awa", "Admis"],
        ]
    )
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    doc.build([table])

    resultat = parser_fichier(chemin, TypeFichier.PDF)

    assert resultat.nombre_lignes == 1
    assert resultat.lignes[0].donnees["numero_pv"] == "001"
    assert "rang_numerique" not in resultat.lignes[0].donnees


def test_parser_fichier_pdf_scan_route_vers_le_parser_fonction_publique(tmp_path) -> None:
    chemin = tmp_path / "scan.pdf"
    image = Image.new("RGB", (1400, 200), "white")
    dessin = ImageDraw.Draw(image)
    dessin.text((30, 20), "ADMISSIBLES", font=_FONT, fill="black")
    dessin.text(
        (30, 60),
        "1° TRAORE AWA 000042-120-03 B19876543 15/05/98",
        font=_FONT,
        fill="black",
    )
    image.save(str(chemin), "PDF")

    resultat = parser_fichier(chemin, TypeFichier.PDF)

    assert resultat.nombre_lignes == 1
    assert resultat.lignes[0].donnees["numero_recepisse"] == "000042"
    assert resultat.lignes[0].donnees["decision"] == "ADMISSIBLE"
