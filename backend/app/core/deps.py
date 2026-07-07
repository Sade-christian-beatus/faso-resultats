import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token, decode_candidat_access_token
from app.database import get_db
from app.models import Administration, RoleUtilisateur, Utilisateur
from app.models.profil_candidat import ProfilCandidat, StatutProfilCandidat

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
    administration (cas des comptes SUPER_ADMIN/SUPPORT, réservés aux routes de
    gestion multi-tenant — voir `get_current_super_admin`)."""
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


async def get_current_super_admin(
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
) -> Utilisateur:
    """Réserve une route à l'équipe plateforme (docs/PIVOT_SAAS_B2G.md § 8, item 8) :
    gestion des `Administration` (tenants) et provisionnement de leur premier
    utilisateur. Un SUPPORT (lecture seule plateforme) n'a pas accès à ces routes
    d'écriture — seul SUPER_ADMIN peut créer/modifier une administration."""
    if current_utilisateur.role != RoleUtilisateur.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Réservé aux comptes SUPER_ADMIN de la plateforme.",
        )
    return current_utilisateur


async def get_current_profil_candidat(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> ProfilCandidat:
    """Authentification candidat, totalement distincte de `get_current_utilisateur` :
    un token émis pour l'espace admin ne peut jamais authentifier une route candidat, et
    inversement (audience JWT dédiée — voir docs/PROFIL_CANDIDAT_UNIFIE.md § 11)."""
    try:
        profil_id = uuid.UUID(decode_candidat_access_token(credentials.credentials))
    except (JWTError, ValueError) as exc:
        raise _CREDENTIALS_ERROR from exc

    profil = await db.get(ProfilCandidat, profil_id)
    if profil is None or profil.statut != StatutProfilCandidat.ACTIF:
        raise _CREDENTIALS_ERROR
    return profil
