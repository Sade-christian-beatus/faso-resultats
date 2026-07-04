from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

from app.services.parsers.pdf_type_detector import detecter_type_pdf


def test_detecter_type_pdf_reconnait_un_pdf_natif(tmp_path) -> None:
    chemin = tmp_path / "natif.pdf"
    doc = SimpleDocTemplate(str(chemin), pagesize=A4)
    doc.build([Paragraph("Un vrai texte numérique.", getSampleStyleSheet()["Normal"])])

    assert detecter_type_pdf(str(chemin)) == "NATIF"


def test_detecter_type_pdf_reconnait_un_scan(tmp_path) -> None:
    chemin = tmp_path / "scan.pdf"
    image = Image.new("RGB", (400, 300), "white")
    image.save(str(chemin), "PDF")

    assert detecter_type_pdf(str(chemin)) == "SCAN"
