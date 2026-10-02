from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

# The client IP comes from the TCP connection. Behind the production reverse proxy,
# uvicorn runs with --proxy-headers so that this is the visitor's IP (taken from
# X-Forwarded-For, which nginx overwrites with the real peer address) and not the
# proxy's: otherwise every visitor would share a single quota.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_settings().rate_limit_storage_uri,
)
