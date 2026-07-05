import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.models import Administration, Utilisateur

_bearer_scheme = HTTPBearer()

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Identifiants invalides ou expirés",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_utilisateur(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Utilisateur:
    try:
        utilisateur_id = uuid.UUID(decode_access_token(credentials.credentials))
    except (JWTError, ValueError) as exc:
        raise _CREDENTIALS_ERROR from exc

    utilisateur = await db.get(Utilisateur, utilisateur_id)
    if utilisateur is None or not utilisateur.actif:
        raise _CREDENTIALS_ERROR
    return utilisateur


async def get_current_administration(
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
    db: AsyncSession = Depends(get_db),
) -> Administration:
    """Résout le tenant courant à partir de l'utilisateur authentifié — voir
    docs/MULTI_TENANCY.md. Adapté en dependency FastAPI plutôt qu'en middleware ASGI
    pour rester cohérent avec `get_current_utilisateur`, déjà utilisé de cette façon
    dans tout le projet.

    Refuse toute requête scopée par tenant si l'utilisateur n'est rattaché à aucune
    administration (cas des comptes SUPER_ADMIN/SUPPORT, réservés aux futures routes
    de gestion multi-tenant, pas encore implémentées)."""
    if current_utilisateur.administration_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce compte n'est rattaché à aucune administration : réservé aux "
            "rôles plateforme (SUPER_ADMIN/SUPPORT), qui n'ont pas encore accès à ces "
            "routes scopées par tenant.",
        )

    administration = await db.get(Administration, current_utilisateur.administration_id)
    if administration is None:
        raise HTTPException(status_code=404, detail="Administration introuvable")
    return administration
