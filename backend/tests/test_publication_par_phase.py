"""Phased publication end to end through the API (docs/CONTEXTE_METIER.md § 2.4).

Scenario: a concours paramilitaire in 3 phases. Phase 1 lists come in, the phase is
closed, phase 2 lists arrive centre by centre, then phase 2 is closed.
"""

import io

import openpyxl
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_clear
from app.models import Resultat

PHASES = ["EPREUVES_SPORTIVES", "ADMISSIBILITE", "ADMISSION_DEFINITIVE"]
CNIB_CANDIDAT = "B00000001"  # CNIB of the `candidat_profil` fixture


def _liste(lignes: list[tuple[str, str, str]]) -> bytes:
    """(numero_pv, jury, cnib) rows; the decision comes from `decision_par_defaut`."""
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.append(["Numéro PV", "Jury", "Nom", "Prénom", "N°CNIB"])
    for pv, jury, cnib in lignes:
        feuille.append([pv, jury, "KABORE", "Ali", cnib])
    buffer = io.BytesIO()
    classeur.save(buffer)
    return buffer.getvalue()


async def _creer_concours(client: AsyncClient, admin_headers: dict) -> str:
    reponse = await client.post(
        "/api/v1/admin/exams",
        json={
            "type_examen": "CONCOURS_DIRECT",
            "annee": 2026,
            "libelle": "Gendarmerie 2026",
            "phases_publication": PHASES,
        },
        headers=admin_headers,
    )
    assert reponse.status_code == 201, reponse.text
    return reponse.json()["id"]


async def _importer(
    client: AsyncClient,
    admin_headers: dict,
    examen_id: str,
    lignes: list[tuple[str, str, str]],
    *,
    phase: str | None,
    decision: str = "APTE",
):
    data = {"examen_id": examen_id, "type_fichier": "EXCEL", "decision_par_defaut": decision}
    if phase:
        data["phase"] = phase
    return await client.post(
        "/api/v1/admin/ingestions",
        data=data,
        files={
            "file": (
                "liste.xlsx",
                _liste(lignes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=admin_headers,
    )


async def _publier_liste(client, admin_headers, examen_id, lignes, *, phase, decision="APTE"):
    upload = await _importer(
        client, admin_headers, examen_id, lignes, phase=phase, decision=decision
    )
    assert upload.status_code == 201, upload.text
    publication = await client.post(
        f"/api/v1/admin/ingestions/{upload.json()['id']}/publish", headers=admin_headers
    )
    assert publication.status_code == 200, publication.text


async def _cloturer(client, admin_headers, examen_id, phase):
    return await client.post(
        f"/api/v1/admin/exams/{examen_id}/phases/{phase}/close", headers=admin_headers
    )


async def _parcours(client: AsyncClient, examen_id: str, pv: str) -> list[tuple]:
    reponse = await client.get(
        "/api/v1/public/results/progress", params={"examen_id": examen_id, "numero_pv": pv}
    )
    assert reponse.status_code == 200, reponse.text
    [parcours] = reponse.json()
    return [(e["phase"], e["statut_phase"], e["situation"]) for e in parcours["etapes"]]


@pytest.mark.asyncio
async def test_creation_refuse_une_phase_en_double(
    client: AsyncClient, admin_headers: dict
) -> None:
    reponse = await client.post(
        "/api/v1/admin/exams",
        json={
            "type_examen": "CONCOURS_DIRECT",
            "annee": 2026,
            "libelle": "X",
            "phases_publication": ["ADMISSIBILITE", "ADMISSIBILITE"],
        },
        headers=admin_headers,
    )
    assert reponse.status_code == 422


@pytest.mark.asyncio
async def test_import_exige_la_phase_et_respecte_l_ordre(
    client: AsyncClient, admin_headers: dict
) -> None:
    examen_id = await _creer_concours(client, admin_headers)
    lignes = [("001", "A", "B11111111")]

    sans_phase = await _importer(client, admin_headers, examen_id, lignes, phase=None)
    assert sans_phase.status_code == 422
    assert "précisez à quelle phase" in sans_phase.json()["detail"]

    trop_tot = await _importer(client, admin_headers, examen_id, lignes, phase="ADMISSIBILITE")
    assert trop_tot.status_code == 409
    assert "EPREUVES_SPORTIVES doit être clôturée" in trop_tot.json()["detail"]


@pytest.mark.asyncio
async def test_parcours_complet_d_un_concours_paramilitaire(
    client: AsyncClient, admin_headers: dict, db_session: AsyncSession
) -> None:
    examen_id = await _creer_concours(client, admin_headers)
    # Phase 1: three candidates apt, in two lists (two centres).
    await _publier_liste(
        client, admin_headers, examen_id, [("001", "A", "B1"), ("002", "A", "B2")], phase=PHASES[0]
    )
    await _publier_liste(client, admin_headers, examen_id, [("003", "B", "B3")], phase=PHASES[0])
    await client.post(f"/api/v1/admin/exams/{examen_id}/publish", headers=admin_headers)

    resultat = (
        await db_session.execute(select(Resultat).where(Resultat.numero_pv == "001"))
    ).scalar_one()
    assert resultat.phase.value == "EPREUVES_SPORTIVES"
    assert resultat.phase_suivante_attendue.value == "ADMISSIBILITE"
    assert resultat.date_publication_phase is not None

    assert await _parcours(client, examen_id, "001") == [
        ("EPREUVES_SPORTIVES", "EN_COURS", "RESULTAT"),
        ("ADMISSIBILITE", "A_VENIR", "A_VENIR"),
        ("ADMISSION_DEFINITIVE", "A_VENIR", "A_VENIR"),
    ]

    assert (await _cloturer(client, admin_headers, examen_id, PHASES[0])).status_code == 200

    # Phase 2, first centre only: 001 is admissible, 002 is not on it (yet).
    await _publier_liste(
        client,
        admin_headers,
        examen_id,
        [("001", "A", "B1")],
        phase=PHASES[1],
        decision="ADMISSIBLE",
    )
    parcours_002 = await _parcours(client, examen_id, "002")
    assert parcours_002[1] == ("ADMISSIBILITE", "EN_COURS", "EN_ATTENTE")

    # Second centre published, then the phase is closed: now 002 is told.
    await _publier_liste(
        client,
        admin_headers,
        examen_id,
        [("003", "B", "B3")],
        phase=PHASES[1],
        decision="ADMISSIBLE",
    )
    assert (await _cloturer(client, admin_headers, examen_id, PHASES[1])).status_code == 200

    await cache_clear()  # lookups above were cached for cache_ttl_seconds
    assert await _parcours(client, examen_id, "002") == [
        ("EPREUVES_SPORTIVES", "CLOTUREE", "RESULTAT"),
        ("ADMISSIBILITE", "CLOTUREE", "NE_FIGURE_PAS"),
        ("ADMISSION_DEFINITIVE", "A_VENIR", "NON_CONCERNE"),
    ]
    assert await _parcours(client, examen_id, "001") == [
        ("EPREUVES_SPORTIVES", "CLOTUREE", "RESULTAT"),
        ("ADMISSIBILITE", "CLOTUREE", "RESULTAT"),
        ("ADMISSION_DEFINITIVE", "A_VENIR", "A_VENIR"),
    ]

    # The plain /results lookup returns every phase row of the candidate.
    lignes = (
        await client.get(
            "/api/v1/public/results", params={"examen_id": examen_id, "numero_pv": "001"}
        )
    ).json()
    assert sorted(r["phase"] for r in lignes) == ["ADMISSIBILITE", "EPREUVES_SPORTIVES"]


@pytest.mark.asyncio
async def test_cloture_refusee_si_une_liste_attend_validation(
    client: AsyncClient, admin_headers: dict
) -> None:
    examen_id = await _creer_concours(client, admin_headers)
    assert (await _cloturer(client, admin_headers, examen_id, PHASES[0])).status_code == 409

    await _publier_liste(client, admin_headers, examen_id, [("001", "A", "B1")], phase=PHASES[0])
    en_attente = await _importer(
        client, admin_headers, examen_id, [("002", "A", "B2")], phase=PHASES[0]
    )
    assert en_attente.status_code == 201

    refus = await _cloturer(client, admin_headers, examen_id, PHASES[0])
    assert refus.status_code == 409
    assert "en attente de validation" in refus.json()["detail"]


@pytest.mark.asyncio
async def test_phase_cloturee_n_accepte_plus_de_liste(
    client: AsyncClient, admin_headers: dict
) -> None:
    examen_id = await _creer_concours(client, admin_headers)
    await _publier_liste(client, admin_headers, examen_id, [("001", "A", "B1")], phase=PHASES[0])
    en_attente = await _importer(
        client, admin_headers, examen_id, [("002", "A", "B2")], phase=PHASES[0]
    )
    await client.post(
        f"/api/v1/admin/ingestions/{en_attente.json()['id']}/reject", headers=admin_headers
    )
    assert (await _cloturer(client, admin_headers, examen_id, PHASES[0])).status_code == 200

    tardive = await _importer(
        client, admin_headers, examen_id, [("009", "A", "B9")], phase=PHASES[0]
    )
    assert tardive.status_code == 409
    assert "déjà clôturée" in tardive.json()["detail"]
    deuxieme_cloture = await _cloturer(client, admin_headers, examen_id, PHASES[0])
    assert deuxieme_cloture.status_code == 409


@pytest.mark.asyncio
async def test_liste_importee_deux_fois_refusee_sans_erreur_500(
    client: AsyncClient, admin_headers: dict
) -> None:
    examen_id = await _creer_concours(client, admin_headers)
    lignes = [("001", "A", "B1"), ("002", "A", "B2")]
    await _publier_liste(client, admin_headers, examen_id, lignes, phase=PHASES[0])

    doublon = await _importer(client, admin_headers, examen_id, lignes, phase=PHASES[0])
    publication = await client.post(
        f"/api/v1/admin/ingestions/{doublon.json()['id']}/publish", headers=admin_headers
    )
    assert publication.status_code == 409
    assert "PV 001 (A)" in publication.json()["detail"]


@pytest.mark.asyncio
async def test_examen_a_publication_unique_inchange(
    client: AsyncClient, admin_headers: dict
) -> None:
    creation = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )
    examen_id = creation.json()["id"]
    await _publier_liste(client, admin_headers, examen_id, [("001", "A", "B1")], phase=None)
    await client.post(f"/api/v1/admin/exams/{examen_id}/publish", headers=admin_headers)

    assert await _parcours(client, examen_id, "001") == [
        ("RESULTAT_UNIQUE", "EN_COURS", "RESULTAT")
    ]


@pytest.mark.asyncio
async def test_dashboard_candidat_suit_les_phases_sans_otp(
    client: AsyncClient, admin_headers: dict, candidat_headers: dict
) -> None:
    """Regression: several phase rows for the same candidate were mistaken for several
    juries sharing a PV number, forcing an OTP fallback."""
    examen_id = await _creer_concours(client, admin_headers)
    await _publier_liste(
        client,
        admin_headers,
        examen_id,
        [("001", "A", CNIB_CANDIDAT), ("002", "A", "B2")],
        phase=PHASES[0],
    )
    await client.post(f"/api/v1/admin/exams/{examen_id}/publish", headers=admin_headers)
    examen_public = (await client.get("/api/v1/public/exams")).json()[0]

    candidature = await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": examen_public["administration_id"],
            "examen_id": examen_id,
            "numero_recepisse": "001",
        },
        headers=candidat_headers,
    )
    assert candidature.status_code == 201, candidature.text
    assert candidature.json()["statut_verification"] == "VERIFIE_AUTO"

    await _cloturer(client, admin_headers, examen_id, PHASES[0])
    await _publier_liste(
        client,
        admin_headers,
        examen_id,
        [("001", "A", CNIB_CANDIDAT)],
        phase=PHASES[1],
        decision="ADMISSIBLE",
    )

    [suivie] = (await client.get("/api/v1/candidat/candidatures", headers=candidat_headers)).json()
    assert suivie["statut_verification"] == "VERIFIE_AUTO"
    assert suivie["dernier_resultat_phase"] == "ADMISSIBILITE"
    assert suivie["dernier_resultat_statut"] == "ADMISSIBLE"

    # Closing phase 2 leaves a candidate who is on its list untouched.
    await _cloturer(client, admin_headers, examen_id, PHASES[1])
    [toujours] = (
        await client.get("/api/v1/candidat/candidatures", headers=candidat_headers)
    ).json()
    assert toujours["dernier_resultat_statut"] == "ADMISSIBLE"  # on the list: unchanged


@pytest.mark.asyncio
async def test_dashboard_candidat_absent_apres_cloture(
    client: AsyncClient, admin_headers: dict, candidat_headers: dict
) -> None:
    examen_id = await _creer_concours(client, admin_headers)
    await _publier_liste(
        client,
        admin_headers,
        examen_id,
        [("001", "A", CNIB_CANDIDAT), ("002", "A", "B2")],
        phase=PHASES[0],
    )
    await client.post(f"/api/v1/admin/exams/{examen_id}/publish", headers=admin_headers)
    examen_public = (await client.get("/api/v1/public/exams")).json()[0]
    await client.post(
        "/api/v1/candidat/candidatures",
        json={
            "administration_id": examen_public["administration_id"],
            "examen_id": examen_id,
            "numero_recepisse": "001",
        },
        headers=candidat_headers,
    )
    await _cloturer(client, admin_headers, examen_id, PHASES[0])
    await _publier_liste(
        client,
        admin_headers,
        examen_id,
        [("002", "A", "B2")],
        phase=PHASES[1],
        decision="ADMISSIBLE",
    )

    [avant] = (await client.get("/api/v1/candidat/candidatures", headers=candidat_headers)).json()
    assert avant["dernier_resultat_phase"] == "EPREUVES_SPORTIVES"  # phase 2 still open

    await _cloturer(client, admin_headers, examen_id, PHASES[1])
    [apres] = (await client.get("/api/v1/candidat/candidatures", headers=candidat_headers)).json()
    assert apres["dernier_resultat_phase"] == "ADMISSIBILITE"
    assert apres["dernier_resultat_statut"] == "NE FIGURE PAS SUR LA LISTE"
