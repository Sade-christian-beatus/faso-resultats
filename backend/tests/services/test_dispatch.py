import pytest
from PIL import Image, ImageDraw, ImageFont
from pytesseract import TesseractNotFoundError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from app.models import TypeFichier
from app.services.ingestion import dispatch
from app.services.ingestion.dispatch import FichierIllisibleError, parser_fichier

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


@pytest.mark.parametrize(
    ("nom", "contenu", "type_fichier"),
    [
        ("corrompu.xlsx", b"pas un classeur", TypeFichier.EXCEL),
        ("corrompu.pdf", b"pas un pdf", TypeFichier.PDF),
        ("corrompu.pdf", b"%PDF-1.4 tronque", TypeFichier.PDF_OCR),
    ],
)
def test_parser_fichier_illisible_leve_une_erreur_metier(
    tmp_path, nom, contenu, type_fichier
) -> None:
    """Regression (audit 2026-11-16, M1): an unreadable file used to raise whatever the
    parsing library raised (BadZipFile, PDFSyntaxError...), turned into a 500."""
    chemin = tmp_path / nom
    chemin.write_bytes(contenu)

    with pytest.raises(FichierIllisibleError):
        parser_fichier(chemin, type_fichier)


def test_parser_fichier_outil_ocr_absent_n_est_pas_un_fichier_illisible(
    tmp_path, monkeypatch
) -> None:
    """A server missing tesseract is a deployment problem: it must not be reported to
    the admin as a corrupted file."""

    def _tesseract_absent(*args, **kwargs):
        raise TesseractNotFoundError()

    monkeypatch.setitem(dispatch._PARSEURS, TypeFichier.PDF_OCR, _tesseract_absent)

    with pytest.raises(TesseractNotFoundError):
        parser_fichier(tmp_path / "scan.pdf", TypeFichier.PDF_OCR)
