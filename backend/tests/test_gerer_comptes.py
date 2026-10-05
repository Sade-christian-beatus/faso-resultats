"""Script de gestion des comptes admin (backend/gerer_comptes.py)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import hash_password
from app.models import RoleUtilisateur, Utilisateur
from app.services.admin.login_lockout_service import AdminLoginLockoutService
from gerer_comptes import (
    ErreurCompte,
    changer_mot_de_passe,
    changer_statut,
    creer_super_admin,
    debloquer,
    lister,
)

settings = get_settings()

EMAIL = "admin@ocecos.bf"
ANCIEN = "ChangeMe123!"
NOUVEAU = "Nouveau-Mdp-2026"


async def _login(client: AsyncClient, email: str, password: str) -> int:
    reponse = await client.post("/api/v1/admin/login", json={"email": email, "password": password})
    return reponse.status_code


@pytest.fixture
async def utilisateur(db_session: AsyncSession) -> Utilisateur:
    utilisateur = Utilisateur(
        email=EMAIL,
        mot_de_passe_hash=hash_password(ANCIEN),
        nom_complet="Admin",
        role=RoleUtilisateur.SUPER_ADMIN,
    )
    db_session.add(utilisateur)
    await db_session.commit()
    return utilisateur


async def test_changer_mot_de_passe(client, db_session, utilisateur) -> None:
    await changer_mot_de_passe(db_session, EMAIL, NOUVEAU)

    assert await _login(client, EMAIL, ANCIEN) == 401
    assert await _login(client, EMAIL, NOUVEAU) == 200


async def test_changer_mot_de_passe_leve_le_verrouillage(client, db_session, utilisateur) -> None:
    for _ in range(settings.admin_login_max_tentatives):
        await AdminLoginLockoutService.enregistrer_echec(EMAIL)
    assert await AdminLoginLockoutService.est_verrouille(EMAIL)

    await changer_mot_de_passe(db_session, EMAIL, NOUVEAU)

    assert not await AdminLoginLockoutService.est_verrouille(EMAIL)


async def test_debloquer(utilisateur) -> None:
    for _ in range(settings.admin_login_max_tentatives):
        await AdminLoginLockoutService.enregistrer_echec(EMAIL)

    await debloquer(EMAIL)

    assert not await AdminLoginLockoutService.est_verrouille(EMAIL)


async def test_mot_de_passe_trop_court_refuse(db_session, utilisateur) -> None:
    with pytest.raises(ErreurCompte):
        await changer_mot_de_passe(db_session, EMAIL, "court")


async def test_compte_inconnu(db_session) -> None:
    with pytest.raises(ErreurCompte):
        await changer_mot_de_passe(db_session, "inconnu@exemple.bf", NOUVEAU)


async def test_creer_super_admin(client, db_session) -> None:
    await creer_super_admin(db_session, "chef@faso-resultats.bf", "Chef", NOUVEAU)

    comptes = await lister(db_session)
    assert [(u.email, u.role, u.administration_id) for u in comptes] == [
        ("chef@faso-resultats.bf", RoleUtilisateur.SUPER_ADMIN, None)
    ]
    assert await _login(client, "chef@faso-resultats.bf", NOUVEAU) == 200


async def test_creer_super_admin_email_existant_refuse(db_session, utilisateur) -> None:
    with pytest.raises(ErreurCompte):
        await creer_super_admin(db_session, EMAIL, "Doublon", NOUVEAU)


async def test_desactiver_puis_activer(client, db_session, utilisateur) -> None:
    await changer_statut(db_session, EMAIL, actif=False)
    assert await _login(client, EMAIL, ANCIEN) == 401

    await changer_statut(db_session, EMAIL, actif=True)
    assert await _login(client, EMAIL, ANCIEN) == 200
