"""CNIB, date and place of birth encrypted at rest in `resultats` and in the raw copies
(`donnees_brutes`, `ingestions.apercu_donnees`) — audit 2026-08-17.

These tests read the database with raw SQL: an ORM round-trip alone would pass even if
nothing were encrypted.
"""

import io
from datetime import date

import openpyxl
import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_deterministe
from app.models import Resultat

CNIB = "B14863543"
LIEU = "Koudougou"
VALEURS_EN_CLAIR = (CNIB, "2001-02-15", "15/02/01", LIEU)


def _xlsx_concours() -> bytes:
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.append(
        ["Numéro PV", "Jury", "Nom", "Prénom", "N°CNIB", "Date de naissance", "Lieu de naissance"]
    )
    feuille.append(["005924", "Centre 06", "BAYALA", "Jean", CNIB, "15/02/01", LIEU])
    buffer = io.BytesIO()
    classeur.save(buffer)
    return buffer.getvalue()


async def _importer(client: AsyncClient, admin_headers: dict, *, publier: bool) -> str:
    examen = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "CONCOURS_DIRECT", "annee": 2026, "libelle": "Douanes 2026"},
        headers=admin_headers,
    )
    upload = await client.post(
        "/api/v1/admin/ingestions",
        data={
            "examen_id": examen.json()["id"],
            "type_fichier": "EXCEL",
            "decision_par_defaut": "ADMISSIBLE",
        },
        files={
            "file": (
                "douanes.xlsx",
                _xlsx_concours(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=admin_headers,
    )
    assert upload.status_code == 201, upload.text
    assert upload.json()["nombre_erreurs"] == 0
    ingestion_id = upload.json()["id"]
    if publier:
        publication = await client.post(
            f"/api/v1/admin/ingestions/{ingestion_id}/publish", headers=admin_headers
        )
        assert publication.status_code == 200
    return ingestion_id


def _aucune_valeur_en_clair(valeur_brute: str | None) -> None:
    assert valeur_brute is not None
    for en_clair in VALEURS_EN_CLAIR:
        assert en_clair not in valeur_brute


@pytest.mark.asyncio
async def test_identite_chiffree_en_base_et_lisible_via_l_orm(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    await _importer(client, admin_headers, publier=True)

    brut = (
        await db_session.execute(
            text(
                "SELECT numero_cnib, date_naissance, lieu_naissance, donnees_brutes "
                "FROM resultats"
            )
        )
    ).one()
    for colonne in brut:
        _aucune_valeur_en_clair(colonne)

    resultat = (await db_session.execute(select(Resultat))).scalar_one()
    assert resultat.numero_cnib == CNIB
    assert resultat.date_naissance == date(2001, 2, 15)
    assert resultat.lieu_naissance == LIEU
    assert CNIB in resultat.donnees_brutes.values()


@pytest.mark.asyncio
async def test_hash_cnib_renseigne_pour_la_recherche_indexee(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    await _importer(client, admin_headers, publier=True)

    requete = text("SELECT numero_cnib_hash FROM resultats")
    hash_en_base = (await db_session.execute(requete)).scalar()
    assert hash_en_base == hash_deterministe(CNIB)


@pytest.mark.asyncio
async def test_apercu_d_ingestion_chiffre_en_base_et_lisible_par_l_admin(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    ingestion_id = await _importer(client, admin_headers, publier=False)

    apercu_brut = (await db_session.execute(text("SELECT apercu_donnees FROM ingestions"))).scalar()
    _aucune_valeur_en_clair(apercu_brut)

    # The admin preview (human validation before publishing) still shows the data.
    apercu = await client.get(f"/api/v1/admin/ingestions/{ingestion_id}", headers=admin_headers)
    assert apercu.json()["lignes"][0]["donnees"]["numero_cnib"] == CNIB


def test_hash_cnib_suit_la_valeur_du_cnib() -> None:
    resultat = Resultat(numero_cnib=CNIB)
    assert resultat.numero_cnib_hash == hash_deterministe(CNIB)

    resultat.numero_cnib = None
    assert resultat.numero_cnib_hash is None

    assert Resultat().numero_cnib_hash is None
