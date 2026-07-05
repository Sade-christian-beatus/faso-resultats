from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import get_settings
from app.core.deps import get_current_utilisateur
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models import Utilisateur
from app.schemas.auth import LoginRequest, TokenResponse, UtilisateurOut

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
    description="Authentifie un utilisateur (toute administration ou plateforme) et "
    "renvoie un token JWT.",
)
@limiter.limit(settings.rate_limit_login)
async def login(
    request: Request, credentials: LoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    result = await db.execute(select(Utilisateur).where(Utilisateur.email == credentials.email))
    utilisateur = result.scalar_one_or_none()

    if (
        utilisateur is None
        or not utilisateur.actif
        or not verify_password(credentials.password, utilisateur.mot_de_passe_hash)
    ):
        raise _INVALID_CREDENTIALS

    utilisateur.derniere_connexion = func.now()
    await db.commit()

    token = create_access_token(subject=str(utilisateur.id))
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UtilisateurOut,
    summary="Profil de l'utilisateur connecté",
    description="Renvoie les informations de l'utilisateur authentifié par le token "
    "JWT, avec son administration de rattachement (absente pour les rôles plateforme).",
)
async def me(current_utilisateur: Utilisateur = Depends(get_current_utilisateur)) -> Utilisateur:
    return current_utilisateur
