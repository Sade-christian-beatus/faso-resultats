import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Deux audiences JWT distinctes (admin / candidat) : un token émis pour l'un ne peut
# jamais authentifier une route de l'autre, même si la clé de signature est partagée
# (docs/PROFIL_CANDIDAT_UNIFIE.md § 11, "deux middlewares d'authentification distincts").
_AUD_ADMIN = "admin"
_AUD_CANDIDAT = "candidat"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


def hash_deterministe(valeur: str) -> str:
    """Hash HMAC-SHA256 stable d'une donnée sensible (CNIB, téléphone), pour permettre
    une recherche/unicité en base sans jamais indexer la valeur en clair
    (docs/PROFIL_CANDIDAT_UNIFIE.md § 11, « indexer sur un hash déterministe »)."""
    return hmac.new(
        settings.candidat_hash_pepper.encode(), valeur.encode(), hashlib.sha256
    ).hexdigest()


_PREFIXE_CLE_API = "frb_live_"


def generer_cle_api() -> str:
    """Clé API B2B en clair (docs/ROADMAP.md § Phase 4) : générée une seule fois côté
    serveur, jamais reconstructible ensuite — seul son hash est conservé (voir
    `hash_cle_api`)."""
    return f"{_PREFIXE_CLE_API}{secrets.token_urlsafe(32)}"


def prefixe_affichable(cle_api: str) -> str:
    """Fragment non sensible de la clé, conservé en clair pour que le partenaire
    puisse identifier laquelle de ses clés est laquelle sans revoir le secret complet."""
    return cle_api[: len(_PREFIXE_CLE_API) + 8]


def hash_cle_api(cle_api: str) -> str:
    """Hash HMAC-SHA256 stable, avec un pepper dédié (`api_key_pepper`) distinct de
    celui des données candidat — permet la recherche en base sans jamais indexer la
    clé en clair, comme `hash_deterministe` pour le CNIB/téléphone."""
    return hmac.new(settings.api_key_pepper.encode(), cle_api.encode(), hashlib.sha256).hexdigest()


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire, "aud": _AUD_ADMIN}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Retourne l'identifiant admin (sub) porté par le token. Lève JWTError si invalide,
    expiré, ou émis pour une autre audience (ex. token candidat)."""
    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm], audience=_AUD_ADMIN
    )
    subject = payload.get("sub")
    if subject is None:
        raise JWTError("Token sans sujet")
    return subject


def create_candidat_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.candidat_jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire, "aud": _AUD_CANDIDAT}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_candidat_access_token(token: str) -> str:
    """Retourne l'identifiant candidat (sub) porté par le token. Lève JWTError si
    invalide, expiré, ou émis pour une autre audience (ex. token admin)."""
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=_AUD_CANDIDAT,
    )
    subject = payload.get("sub")
    if subject is None:
        raise JWTError("Token sans sujet")
    return subject
