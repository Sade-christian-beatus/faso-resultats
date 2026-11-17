"""End-to-end regressions for the ingestion bugs found by the 2026-11-16 audit
(docs/AUDIT_2026-11-16.md): real Excel dates (C1), values typed in the correction
screen (E5), unreadable files (M1)."""

from datetime import date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ingestion, Resultat
from tests.test_admin_ingestions import _construire_xlsx, _creer_examen

_TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


async def _upload(
    client: AsyncClient, admin_headers: dict, contenu: bytes, nom: str = "resultats.xlsx"
):
    examen_id = await _creer_examen(client, admin_headers)
    return await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen_id, "type_fichier": "EXCEL"},
        files={"file": (nom, contenu, _TYPE_XLSX)},
        headers=admin_headers,
    )


async def _publier(client: AsyncClient, admin_headers: dict, ingestion_id: str):
    return await client.post(
        f"/api/v1/admin/ingestions/{ingestion_id}/publish", headers=admin_headers
    )


async def _resultat_unique(db_session: AsyncSession) -> Resultat:
    return (await db_session.execute(select(Resultat))).scalar_one()


@pytest.mark.asyncio
async def test_excel_avec_cellule_date_typee_se_publie(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    contenu = _construire_xlsx(
        [["001", "Ouaga 1", "Traore", "Awa", datetime(2008, 5, 12), "Admis", 13.5]]
    )

    upload = await _upload(client, admin_headers, contenu)
    assert upload.status_code == 201
    assert upload.json()["lignes"][0]["donnees"]["date_naissance"] == "2008-05-12"

    publish = await _publier(client, admin_headers, upload.json()["id"])

    assert publish.status_code == 200
    assert (await _resultat_unique(db_session)).date_naissance == date(2008, 5, 12)


@pytest.mark.asyncio
async def test_valeurs_saisies_en_correction_sont_normalisees_puis_publiees(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    upload = await _upload(
        client,
        admin_headers,
        _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", None, "Admis", 10]]),
    )
    lignes = upload.json()["lignes"]
    lignes[0]["donnees"].update(moyenne="12,5", decision="admis", date_naissance="12/05/2008")

    correction = await client.patch(
        f"/api/v1/admin/ingestions/{upload.json()['id']}",
        json={"lignes": lignes},
        headers=admin_headers,
    )

    assert correction.status_code == 200
    assert correction.json()["nombre_erreurs"] == 0
    donnees = correction.json()["lignes"][0]["donnees"]
    assert donnees["moyenne"] == 12.5
    assert donnees["decision"] == "ADMIS"
    assert donnees["date_naissance"] == "2008-05-12"

    publish = await _publier(client, admin_headers, upload.json()["id"])

    assert publish.status_code == 200
    resultat = await _resultat_unique(db_session)
    assert float(resultat.moyenne) == 12.5
    assert resultat.decision == "ADMIS"
    assert resultat.date_naissance == date(2008, 5, 12)


@pytest.mark.asyncio
async def test_date_illisible_en_correction_bloque_la_publication(
    client: AsyncClient, admin_headers: dict
) -> None:
    upload = await _upload(
        client,
        admin_headers,
        _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", None, "Admis", 10]]),
    )
    lignes = upload.json()["lignes"]
    lignes[0]["donnees"]["date_naissance"] = "31/02/2008"

    correction = await client.patch(
        f"/api/v1/admin/ingestions/{upload.json()['id']}",
        json={"lignes": lignes},
        headers=admin_headers,
    )

    assert correction.json()["nombre_erreurs"] == 1
    assert correction.json()["lignes"][0]["donnees"]["date_naissance"] == "31/02/2008"
    assert (await _publier(client, admin_headers, upload.json()["id"])).status_code == 400


@pytest.mark.asyncio
async def test_apercu_stocke_avant_le_correctif_se_publie(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    """Previews uploaded before the fix carry "2008-05-12T00:00:00" in the database."""
    upload = await _upload(
        client,
        admin_headers,
        _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", None, "Admis", 10]]),
    )
    ingestion = await db_session.get(Ingestion, upload.json()["id"])
    apercu = [dict(ligne) for ligne in ingestion.apercu_donnees]
    apercu[0] = {
        **apercu[0],
        "donnees": {**apercu[0]["donnees"], "date_naissance": "2008-05-12T00:00:00"},
    }
    ingestion.apercu_donnees = apercu
    await db_session.commit()

    publish = await _publier(client, admin_headers, upload.json()["id"])

    assert publish.status_code == 200
    assert (await _resultat_unique(db_session)).date_naissance == date(2008, 5, 12)


@pytest.mark.asyncio
async def test_publication_revalide_les_donnees_sans_se_fier_au_compteur_d_erreurs(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    upload = await _upload(
        client,
        admin_headers,
        _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", None, "Admis", 10]]),
    )
    ingestion = await db_session.get(Ingestion, upload.json()["id"])
    apercu = [dict(ligne) for ligne in ingestion.apercu_donnees]
    apercu[0] = {**apercu[0], "donnees": {**apercu[0]["donnees"], "moyenne": "douze"}}
    ingestion.apercu_donnees = apercu
    ingestion.nombre_erreurs = 0
    await db_session.commit()

    publish = await _publier(client, admin_headers, upload.json()["id"])

    assert publish.status_code == 400
    assert (await db_session.execute(select(func.count()).select_from(Resultat))).scalar_one() == 0


@pytest.mark.asyncio
async def test_upload_xls_refuse_avec_consigne_de_conversion(
    client: AsyncClient, admin_headers: dict
) -> None:
    response = await _upload(client, admin_headers, b"\xd0\xcf\x11\xe0", nom="resultats.xls")

    assert response.status_code == 422
    assert ".xlsx" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_fichier_corrompu_refuse_sans_laisser_de_fichier(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession, tmp_path
) -> None:
    response = await _upload(client, admin_headers, b"pas un classeur", nom="resultats.xlsx")

    assert response.status_code == 422
    assert "n'a pas pu être lu" in response.json()["detail"]
    assert [f for f in tmp_path.rglob("*") if f.is_file()] == []
    assert (await db_session.execute(select(func.count()).select_from(Ingestion))).scalar_one() == 0
