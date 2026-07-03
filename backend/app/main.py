from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.core.rate_limit import limiter
from app.routes import health
from app.routes.admin import auth as admin_auth
from app.routes.admin import exams as admin_exams
from app.routes.admin import ingestions as admin_ingestions
from app.routes.public import results as public_results

settings = get_settings()

app = FastAPI(
    title="Faso Résultats API",
    description="API de consultation des résultats d'examens et concours nationaux du Burkina Faso",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(admin_auth.router)
app.include_router(admin_exams.router)
app.include_router(admin_ingestions.router)
app.include_router(public_results.router)
