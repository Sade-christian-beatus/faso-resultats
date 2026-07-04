from pathlib import Path

from app.models import TypeFichier
from app.services.ingestion.excel_parser import parser_excel
from app.services.ingestion.ocr_parser import parser_ocr
from app.services.ingestion.pdf_parser import parser_pdf
from app.services.ingestion.types import ResultatExtraction
from app.services.parsers.pdf_type_detector import detecter_type_pdf
from app.services.parsers.scan_pdf_parser import parser_pdf_scan

_PARSEURS = {
    TypeFichier.EXCEL: parser_excel,
    TypeFichier.PDF_OCR: parser_ocr,
}


def parser_fichier(
    chemin_fichier: str | Path,
    type_fichier: TypeFichier,
    decision_par_defaut: str | None = None,
) -> ResultatExtraction:
    if type_fichier == TypeFichier.PDF:
        # Détection automatique : certains PDF "natifs" (ex. communiqués de la
        # Fonction publique) sont en réalité des scans sans couche texte, pour
        # lesquels pdfplumber ne trouve aucun tableau — route vers l'OCR spécialisé
        # sans que l'admin ait à le savoir à l'avance.
        parseur = parser_pdf_scan if detecter_type_pdf(chemin_fichier) == "SCAN" else parser_pdf
        return parseur(chemin_fichier, decision_par_defaut)

    return _PARSEURS[type_fichier](chemin_fichier, decision_par_defaut)
