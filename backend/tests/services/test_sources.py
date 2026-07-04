import io

import openpyxl
import pytest

from app.models import TypeFichier
from app.services.sources.file_import_source import FileImportSource
from app.services.sources.stubs import (
    FacebookMonitorSource,
    GouvPdfMonitorSource,
    PressMonitoringSource,
    SigecApiSource,
)


@pytest.mark.asyncio
async def test_file_import_source_delegue_au_dispatch(tmp_path) -> None:
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.append(["Numero PV", "Jury", "Nom", "Prenom", "Decision"])
    feuille.append(["001", "Ouaga 1", "Traore", "Awa", "Admis"])
    buffer = io.BytesIO()
    classeur.save(buffer)
    chemin = tmp_path / "resultats.xlsx"
    chemin.write_bytes(buffer.getvalue())

    source = FileImportSource()
    lignes = await source.fetch_results(
        "examen-id-peu-importe", chemin_fichier=chemin, type_fichier=TypeFichier.EXCEL
    )

    assert len(lignes) == 1
    assert lignes[0].donnees["numero_pv"] == "001"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source_cls",
    [SigecApiSource, GouvPdfMonitorSource, FacebookMonitorSource, PressMonitoringSource],
)
async def test_sources_non_implementees_levent_explicitement(source_cls) -> None:
    with pytest.raises(NotImplementedError):
        await source_cls().fetch_results("examen-id")
