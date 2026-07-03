from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import get_settings
from app.core.deps import get_current_admin
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models import Admin
from app.schemas.auth import AdminOut, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/v1/admin", tags=["admin-auth"])
settings = get_settings()

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email ou mot de passe incorrect",
)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Connexion admin",
    description="Authentifie un administrateur et renvoie un token JWT.",
)
@limiter.limit(settings.rate_limit_login)
async def login(
    request: Request, credentials: LoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    result = await db.execute(select(Admin).where(Admin.email == credentials.email))
    admin = result.scalar_one_or_none()

    if (
        admin is None
        or not admin.actif
        or not verify_password(credentials.password, admin.mot_de_passe_hash)
    ):
        raise _INVALID_CREDENTIALS

    admin.derniere_connexion = func.now()
    await db.commit()

    token = create_access_token(subject=str(admin.id))
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=AdminOut,
    summary="Profil de l'admin connecté",
    description="Renvoie les informations de l'administrateur authentifié par le token JWT.",
)
async def me(current_admin: Admin = Depends(get_current_admin)) -> Admin:
    return current_admin
