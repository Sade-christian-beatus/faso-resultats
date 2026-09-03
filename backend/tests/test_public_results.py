import io

import openpyxl
import pytest
from httpx import AsyncClient


def _construire_xlsx(lignes: list[list]) -> bytes:
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.append(
        ["Numéro PV", "Jury", "Nom", "Prénom", "Date de naissance", "Décision", "Moyenne"]
    )
    for ligne in lignes:
        feuille.append(ligne)
    buffer = io.BytesIO()
    classeur.save(buffer)
    return buffer.getvalue()


async def _publier_examen_avec_resultat(client: AsyncClient, admin_headers: dict) -> dict:
    """Crée un examen, y importe un résultat, publie l'ingestion puis l'examen."""
    exam_response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026"},
        headers=admin_headers,
    )
    examen = exam_response.json()

    contenu = _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", "12/05/2008", "Admis", 13.45]])
    upload = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen["id"], "type_fichier": "EXCEL"},
        files={
            "file": (
                "resultats.xlsx",
                contenu,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=admin_headers,
    )
    ingestion_id = upload.json()["id"]
    await client.post(f"/api/v1/admin/ingestions/{ingestion_id}/publish", headers=admin_headers)
    await client.post(f"/api/v1/admin/exams/{examen['id']}/publish", headers=admin_headers)
    return examen


@pytest.mark.asyncio
async def test_liste_examens_publics_exclut_les_brouillons(
    client: AsyncClient, admin_headers: dict
) -> None:
    await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "CEP", "annee": 2026, "libelle": "CEP 2026 - Brouillon"},
        headers=admin_headers,
    )

    response = await client.get("/api/v1/public/exams")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_liste_examens_publics_inclut_les_publies(
    client: AsyncClient, admin_headers: dict
) -> None:
    examen = await _publier_examen_avec_resultat(client, admin_headers)

    response = await client.get("/api/v1/public/exams")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == examen["id"]


@pytest.mark.asyncio
async def test_recherche_resultat_trouve(client: AsyncClient, admin_headers: dict) -> None:
    examen = await _publier_examen_avec_resultat(client, admin_headers)

    response = await client.get(
        "/api/v1/public/results",
        params={"examen_id": examen["id"], "numero_pv": "001", "jury": "Ouaga 1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["nom"] == "Traore"
    assert body[0]["decision"] == "ADMIS"
    # Données sensibles non exposées publiquement.
    assert "date_naissance" not in body[0]
    assert "lieu_naissance" not in body[0]
    # Phase/rang exposés (nécessaires à l'affichage "Rang / Phase / Prochaine
    # étape" côté clients, ex. app mobile) — RESULTAT_UNIQUE par défaut pour un
    # examen scolaire simple.
    assert body[0]["phase"] == "RESULTAT_UNIQUE"
    assert body[0]["phase_suivante_attendue"] is None


@pytest.mark.asyncio
async def test_recherche_resultat_introuvable(client: AsyncClient, admin_headers: dict) -> None:
    examen = await _publier_examen_avec_resultat(client, admin_headers)

    response = await client.get(
        "/api/v1/public/results",
        params={"examen_id": examen["id"], "numero_pv": "999"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_recherche_resultat_examen_non_publie_invisible(
    client: AsyncClient, admin_headers: dict
) -> None:
    exam_response = await client.post(
        "/api/v1/admin/exams",
        json={"type_examen": "BAC", "annee": 2026, "libelle": "BAC 2026 - Brouillon"},
        headers=admin_headers,
    )
    examen_id = exam_response.json()["id"]

    contenu = _construire_xlsx([["001", "Ouaga 1", "Traore", "Awa", "12/05/2008", "Admis", 13.45]])
    upload = await client.post(
        "/api/v1/admin/ingestions",
        data={"examen_id": examen_id, "type_fichier": "EXCEL"},
        files={
            "file": (
                "resultats.xlsx",
                contenu,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=admin_headers,
    )
    ingestion_id = upload.json()["id"]
    await client.post(f"/api/v1/admin/ingestions/{ingestion_id}/publish", headers=admin_headers)
    # L'examen lui-même reste en DRAFT : le résultat publié via l'ingestion ne doit
    # pas être visible côté public.

    response = await client.get(
        "/api/v1/public/results", params={"examen_id": examen_id, "numero_pv": "001"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_recherche_resultat_utilise_le_cache(
    client: AsyncClient, admin_headers: dict
) -> None:
    examen = await _publier_examen_avec_resultat(client, admin_headers)

    premiere = await client.get(
        "/api/v1/public/results",
        params={"examen_id": examen["id"], "numero_pv": "001", "jury": "Ouaga 1"},
    )
    deuxieme = await client.get(
        "/api/v1/public/results",
        params={"examen_id": examen["id"], "numero_pv": "001", "jury": "Ouaga 1"},
    )

    assert premiere.json() == deuxieme.json()


@pytest.mark.asyncio
async def test_liste_administrations_publiques_expose_les_champs_utiles(
    client: AsyncClient, admin_headers: dict
) -> None:
    """admin_headers crée une administration en statut PILOTE (défaut du modèle) : elle
    doit apparaître dans la liste publique, sans exposer les champs de contact interne."""
    response = await client.get("/api/v1/public/administrations")

    assert response.status_code == 200
    administrations = response.json()
    assert len(administrations) >= 1
    premiere = administrations[0]
    assert "nom_officiel" in premiere
    assert "sigle" in premiere
    assert "contact_referent_email" not in premiere


@pytest.mark.asyncio
async def test_droits_candidat_expose_un_contact_et_les_droits(client: AsyncClient) -> None:
    """Canal de contact dédié (docs/CIL_PROFIL_CANDIDAT.md § 8) pour les demandes qui
    ne passent pas par les endpoints candidat en libre-service."""
    response = await client.get("/api/v1/public/droits-candidat")

    assert response.status_code == 200
    corps = response.json()
    assert "@" in corps["contact_dpo"]
    assert len(corps["droits"]) >= 4
