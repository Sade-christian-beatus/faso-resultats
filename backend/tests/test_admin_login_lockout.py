"""Verrouillage de compte admin après échecs de connexion répétés (audit 2026-08-17) :
protège contre un brute-force distribué sur plusieurs IP, que le rate-limit IP seul
(`RATE_LIMIT_LOGIN`) ne couvre pas."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import hash_password
from app.models import ActionAuditLog, AuditLog, RoleUtilisateur, Utilisateur
from app.services.admin.login_lockout_service import AdminLoginLockoutService

settings = get_settings()

EMAIL = "admin@faso-resultats.bf"
PASSWORD = "ChangeMe123!"


async def _create_utilisateur(db_session: AsyncSession) -> Utilisateur:
    utilisateur = Utilisateur(
        email=EMAIL,
        mot_de_passe_hash=hash_password(PASSWORD),
        nom_complet="Admin",
        role=RoleUtilisateur.SUPER_ADMIN,
    )
    db_session.add(utilisateur)
    await db_session.commit()
    return utilisateur


@pytest.mark.asyncio
async def test_service_verrouille_apres_le_seuil_configure() -> None:
    email = "brute-force-1@faso-resultats.bf"
    assert await AdminLoginLockoutService.est_verrouille(email) is False

    for _ in range(settings.admin_login_max_tentatives - 1):
        await AdminLoginLockoutService.enregistrer_echec(email)
        assert await AdminLoginLockoutService.est_verrouille(email) is False

    await AdminLoginLockoutService.enregistrer_echec(email)
    assert await AdminLoginLockoutService.est_verrouille(email) is True


@pytest.mark.asyncio
async def test_service_verrouille_de_la_meme_facon_un_email_inexistant() -> None:
    """Le mécanisme ne doit pas permettre de deviner si un compte existe : un email
    inconnu se verrouille exactement comme un email réel."""
    email = "ce-compte-nexiste-pas@faso-resultats.bf"

    for _ in range(settings.admin_login_max_tentatives):
        await AdminLoginLockoutService.enregistrer_echec(email)

    assert await AdminLoginLockoutService.est_verrouille(email) is True


@pytest.mark.asyncio
async def test_service_reinitialiser_efface_le_compteur() -> None:
    email = "reset-apres-succes@faso-resultats.bf"
    await AdminLoginLockoutService.enregistrer_echec(email)
    await AdminLoginLockoutService.enregistrer_echec(email)

    await AdminLoginLockoutService.reinitialiser(email)

    for _ in range(settings.admin_login_max_tentatives):
        await AdminLoginLockoutService.enregistrer_echec(email)
    assert await AdminLoginLockoutService.est_verrouille(email) is True


@pytest.mark.asyncio
async def test_flood_de_mauvais_mots_de_passe_finit_par_etre_bloque(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_utilisateur(db_session)

    codes = []
    for _ in range(15):
        response = await client.post(
            "/api/v1/admin/login", json={"email": EMAIL, "password": "mauvais-mot-de-passe"}
        )
        codes.append(response.status_code)

    assert 429 in codes
    # Même avec le bon mot de passe, le compte reste verrouillé tant que la fenêtre
    # n'est pas écoulée.
    ultime = await client.post("/api/v1/admin/login", json={"email": EMAIL, "password": PASSWORD})
    assert ultime.status_code == 429


@pytest.mark.asyncio
async def test_login_echoue_est_journalise(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_utilisateur(db_session)

    await client.post("/api/v1/admin/login", json={"email": EMAIL, "password": "faux"})

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == ActionAuditLog.LOGIN_FAILED)
    )
    log = result.scalar_one()
    assert log.utilisateur_id is not None


@pytest.mark.asyncio
async def test_login_echoue_sur_email_inconnu_est_journalise_sans_utilisateur(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await client.post(
        "/api/v1/admin/login",
        json={"email": "inconnu-audit@faso-resultats.bf", "password": "peu-importe"},
    )

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == ActionAuditLog.LOGIN_FAILED)
    )
    log = result.scalar_one()
    assert log.utilisateur_id is None


@pytest.mark.asyncio
async def test_quelques_echecs_sous_le_seuil_nempechent_pas_la_connexion(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_utilisateur(db_session)

    for _ in range(settings.admin_login_max_tentatives - 2):
        response = await client.post(
            "/api/v1/admin/login", json={"email": EMAIL, "password": "faux"}
        )
        assert response.status_code == 401

    reussie = await client.post("/api/v1/admin/login", json={"email": EMAIL, "password": PASSWORD})
    assert reussie.status_code == 200
