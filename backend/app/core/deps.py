import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.models import Admin

_bearer_scheme = HTTPBearer()

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Identifiants invalides ou expirés",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    try:
        admin_id = uuid.UUID(decode_access_token(credentials.credentials))
    except (JWTError, ValueError) as exc:
        raise _CREDENTIALS_ERROR from exc

    admin = await db.get(Admin, admin_id)
    if admin is None or not admin.actif:
        raise _CREDENTIALS_ERROR
    return admin
