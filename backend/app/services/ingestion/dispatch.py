from pathlib import Path

from app.models import TypeFichier
from app.services.ingestion.excel_parser import parser_excel
from app.services.ingestion.ocr_parser import parser_ocr
from app.services.ingestion.pdf_parser import parser_pdf
from app.services.ingestion.types import ResultatExtraction

_PARSEURS = {
    TypeFichier.EXCEL: parser_excel,
    TypeFichier.PDF: parser_pdf,
    TypeFichier.PDF_OCR: parser_ocr,
}


def parser_fichier(chemin_fichier: str | Path, type_fichier: TypeFichier) -> ResultatExtraction:
    return _PARSEURS[type_fichier](chemin_fichier)
