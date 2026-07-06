import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profil_candidat import ProfilCandidat

_INSCRIPTION_PAYLOAD = {
    "numero_cnib": "B14863543",
    "nom_complet": "TRAORE Awa",
    "date_naissance": "2001-02-15",
    "telephone": "+22670000010",
    "consentement_apdp": True,
    "consentement_apdp_version": "v1",
}


async def _inscrire_et_verifier(client: AsyncClient, payload: dict | None = None) -> dict:
    payload = payload or _INSCRIPTION_PAYLOAD
    reponse = await client.post("/api/v1/candidat/inscription", json=payload)
    code = reponse.json()["code_otp_debug"]
    verif = await client.post(
        "/api/v1/candidat/otp/verify", json={"telephone": payload["telephone"], "code": code}
    )
    return verif.json()


@pytest.mark.asyncio
async def test_inscription_sans_consentement_rejetee(client: AsyncClient) -> None:
    payload = {**_INSCRIPTION_PAYLOAD, "consentement_apdp": False}

    response = await client.post("/api/v1/candidat/inscription", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_inscription_puis_otp_cree_le_compte(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    session = await _inscrire_et_verifier(client)

    assert session["compte_cree"] is True
    assert session["access_token"]

    profil = (await db_session.execute(select(ProfilCandidat))).scalar_one()
    assert profil.nom_complet == "TRAORE Awa"
    assert profil.telephone_verifie is True


@pytest.mark.asyncio
async def test_inscription_avec_cnib_deja_utilise_rejetee(client: AsyncClient) -> None:
    await _inscrire_et_verifier(client)

    response = await client.post(
        "/api/v1/candidat/inscription",
        json={**_INSCRIPTION_PAYLOAD, "telephone": "+22670000099"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_otp_verify_avec_mauvais_code_rejete(client: AsyncClient) -> None:
    await client.post("/api/v1/candidat/inscription", json=_INSCRIPTION_PAYLOAD)

    response = await client.post(
        "/api/v1/candidat/otp/verify",
        json={"telephone": _INSCRIPTION_PAYLOAD["telephone"], "code": "000000"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_sur_compte_existant_ne_recree_pas_de_profil(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _inscrire_et_verifier(client)

    login = await client.post(
        "/api/v1/candidat/login", json={"telephone": _INSCRIPTION_PAYLOAD["telephone"]}
    )
    code = login.json()["code_otp_debug"]
    verif = await client.post(
        "/api/v1/candidat/otp/verify",
        json={"telephone": _INSCRIPTION_PAYLOAD["telephone"], "code": code},
    )

    assert verif.status_code == 200
    assert verif.json()["compte_cree"] is False
    profils = (await db_session.execute(select(ProfilCandidat))).scalars().all()
    assert len(profils) == 1


@pytest.mark.asyncio
async def test_login_sur_numero_inconnu_repond_generique(client: AsyncClient) -> None:
    """Ne doit jamais permettre de deviner si un numéro est inscrit ou non."""
    response = await client.post("/api/v1/candidat/login", json={"telephone": "+22670009999"})

    assert response.status_code == 200
    assert response.json()["code_otp_debug"] is None


@pytest.mark.asyncio
async def test_me_requires_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/candidat/me")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_me_avec_session_valide(client: AsyncClient) -> None:
    session = await _inscrire_et_verifier(client)

    response = await client.get(
        "/api/v1/candidat/me", headers={"Authorization": f"Bearer {session['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json()["nom_complet"] == "TRAORE Awa"


@pytest.mark.asyncio
async def test_delete_me_purge_le_profil(client: AsyncClient, db_session: AsyncSession) -> None:
    session = await _inscrire_et_verifier(client)
    headers = {"Authorization": f"Bearer {session['access_token']}"}

    response = await client.delete("/api/v1/candidat/me", headers=headers)
    assert response.status_code == 204

    profils = (await db_session.execute(select(ProfilCandidat))).scalars().all()
    assert profils == []

    # Le token ne doit plus fonctionner après suppression du compte.
    response = await client.get("/api/v1/candidat/me", headers=headers)
    assert response.status_code == 401
