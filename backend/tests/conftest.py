from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.core.cache import cache_clear
from app.core.rate_limit import limiter
from app.core.security import hash_deterministe, hash_password
from app.database import get_db
from app.main import app
from app.models import Administration, RoleUtilisateur, Utilisateur
from app.models.base import Base
from app.models.profil_candidat import ProfilCandidat
from app.services.candidat.auth_service import AuthCandidatService


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    limiter.reset()


@pytest.fixture(autouse=True)
async def _clear_cache() -> None:
    await cache_clear()


@pytest.fixture(autouse=True)
def _uploads_dir(tmp_path) -> None:
    get_settings().uploads_dir = str(tmp_path)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        # SQLite ne supporte pas les schémas Postgres : les tables du schéma
        # "plateforme" (profil candidat, docs/PROFIL_CANDIDAT_UNIFIE.md § 2) sont créées
        # sans préfixe de schéma en test, tout en gardant le vrai schéma en production.
        execution_options={"schema_translate_map": {"plateforme": None}},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_db_override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _creer_administration_et_headers(
    client: AsyncClient, db_session: AsyncSession, *, code: str, email: str
) -> dict[str, str]:
    administration = Administration(
        code=code,
        nom_officiel=f"Administration {code}",
        sigle=code.upper(),
        ministere_tutelle="Ministère de test",
        contact_referent_nom="Référent Test",
        contact_referent_email=email,
        contact_referent_telephone="+22600000000",
    )
    db_session.add(administration)
    await db_session.commit()
    await db_session.refresh(administration)

    password = "ChangeMe123!"
    db_session.add(
        Utilisateur(
            administration_id=administration.id,
            email=email,
            mot_de_passe_hash=hash_password(password),
            nom_complet="Admin Test",
            role=RoleUtilisateur.ADMIN_ADMINISTRATION,
        )
    )
    await db_session.commit()

    response = await client.post("/api/v1/admin/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, db_session: AsyncSession) -> dict[str, str]:
    """Crée une administration + un utilisateur ADMIN_ADMINISTRATION rattaché, renvoie
    les headers d'autorisation pour les routes admin scopées par tenant."""
    return await _creer_administration_et_headers(
        client, db_session, code="tenant-test", email="admin@faso-resultats.bf"
    )


@pytest.fixture
async def autre_administration_headers(
    client: AsyncClient, db_session: AsyncSession
) -> dict[str, str]:
    """Un second tenant, avec son propre utilisateur — pour les tests d'isolation
    multi-tenant (jamais voir/modifier les données d'une autre administration)."""
    return await _creer_administration_et_headers(
        client, db_session, code="autre-tenant", email="admin@autre-tenant.bf"
    )


async def _creer_profil_candidat(
    db_session: AsyncSession, *, numero_cnib: str, telephone: str
) -> ProfilCandidat:
    profil = ProfilCandidat(
        numero_cnib=numero_cnib,
        numero_cnib_hash=hash_deterministe(numero_cnib),
        nom_complet="Candidat Test",
        date_naissance=date(2000, 1, 1).isoformat(),
        telephone=telephone,
        telephone_hash=hash_deterministe(telephone),
        telephone_verifie=True,
        consentement_apdp_date=datetime.now(UTC),
        consentement_apdp_version="v1",
    )
    db_session.add(profil)
    await db_session.commit()
    await db_session.refresh(profil)
    return profil


@pytest.fixture
async def candidat_profil(db_session: AsyncSession) -> ProfilCandidat:
    """Un profil candidat plateforme, créé directement en base (sans passer par le
    parcours OTP complet) pour les tests qui n'exercent pas spécifiquement l'auth."""
    return await _creer_profil_candidat(
        db_session, numero_cnib="B00000001", telephone="+22670000001"
    )


@pytest.fixture
async def candidat_headers(candidat_profil: ProfilCandidat) -> dict[str, str]:
    token = AuthCandidatService.creer_session(candidat_profil.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def autre_candidat_profil(db_session: AsyncSession) -> ProfilCandidat:
    """Un second profil candidat — pour les tests d'isolation (un candidat ne doit
    jamais voir ou modifier les candidatures d'un autre candidat)."""
    return await _creer_profil_candidat(
        db_session, numero_cnib="B00000002", telephone="+22670000002"
    )


@pytest.fixture
async def autre_candidat_headers(autre_candidat_profil: ProfilCandidat) -> dict[str, str]:
    token = AuthCandidatService.creer_session(autre_candidat_profil.id)
    return {"Authorization": f"Bearer {token}"}
