from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import get_settings
from app.core.deps import get_current_utilisateur
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models import ActionAuditLog, Utilisateur
from app.schemas.auth import LoginRequest, TokenResponse, UtilisateurOut
from app.services.admin.login_lockout_service import AdminLoginLockoutService
from app.services.audit_service import journaliser_audit

router = APIRouter(prefix="/api/v1/admin", tags=["admin-auth"])
settings = get_settings()

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email ou mot de passe incorrect",
)

_ACCOUNT_LOCKED = HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail="Trop de tentatives échouées. Réessayez dans quelques minutes.",
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
    if await AdminLoginLockoutService.est_verrouille(credentials.email):
        raise _ACCOUNT_LOCKED

    result = await db.execute(select(Utilisateur).where(Utilisateur.email == credentials.email))
    utilisateur = result.scalar_one_or_none()

    if (
        utilisateur is None
        or not utilisateur.actif
        or not verify_password(credentials.password, utilisateur.mot_de_passe_hash)
    ):
        await AdminLoginLockoutService.enregistrer_echec(credentials.email)
        await journaliser_audit(
            db,
            utilisateur_id=utilisateur.id if utilisateur else None,
            administration_id=utilisateur.administration_id if utilisateur else None,
            action=ActionAuditLog.LOGIN_FAILED,
            request=request,
        )
        await db.commit()
        raise _INVALID_CREDENTIALS

    await AdminLoginLockoutService.reinitialiser(credentials.email)
    utilisateur.derniere_connexion = func.now()
    await journaliser_audit(
        db,
        utilisateur_id=utilisateur.id,
        administration_id=utilisateur.administration_id,
        action=ActionAuditLog.LOGIN,
        request=request,
    )
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
