import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.cache import cache_get, cache_set
from app.core.deps import get_current_api_key
from app.database import get_db
from app.models import ApiKey, Examen, Resultat, StatutExamen
from app.schemas.public import ExamenPublicOut, ResultatPublicOut
from app.services.b2b.quota_service import consommer_quota

router = APIRouter(prefix="/api/v1/b2b", tags=["b2b"])
settings = get_settings()

_MESSAGE_QUOTA_DEPASSE = (
    "Quota quotidien dépassé pour cette clé API. Contactez la plateforme pour "
    "ajuster votre quota si besoin."
)


async def _appliquer_quota(api_key: ApiKey, db: AsyncSession) -> None:
    if not await consommer_quota(api_key.id, api_key.quota_quotidien):
        raise HTTPException(status_code=429, detail=_MESSAGE_QUOTA_DEPASSE)
    api_key.derniere_utilisation = datetime.now(UTC)
    await db.commit()


@router.get(
    "/exams",
    response_model=list[ExamenPublicOut],
    summary="[B2B] Lister les examens publiés",
    description="Équivalent de GET /api/v1/public/exams, authentifié par clé API "
    "(en-tête X-API-Key) avec un quota quotidien dédié plutôt qu'un rate-limit par IP.",
)
async def list_b2b_exams(
    api_key: ApiKey = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_db),
) -> list[ExamenPublicOut]:
    await _appliquer_quota(api_key, db)

    cle_cache = "public:exams"
    cache = await cache_get(cle_cache)
    if cache is not None:
        return [ExamenPublicOut.model_validate(item) for item in cache]

    result = await db.execute(
        select(Examen)
        .where(Examen.statut == StatutExamen.PUBLISHED)
        .order_by(Examen.annee.desc(), Examen.type_examen)
    )
    examens = [ExamenPublicOut.model_validate(e) for e in result.scalars().all()]
    await cache_set(
        cle_cache, [e.model_dump(mode="json") for e in examens], settings.cache_ttl_seconds
    )
    return examens


@router.get(
    "/results",
    response_model=list[ResultatPublicOut],
    summary="[B2B] Consulter un résultat",
    description="Équivalent de GET /api/v1/public/results, authentifié par clé API "
    "(en-tête X-API-Key) avec un quota quotidien dédié plutôt qu'un rate-limit par IP. "
    "Mêmes champs, mêmes exclusions (pas de date de naissance, lieu de naissance ni "
    "CNIB) — pas d'accès élargi aux données sensibles pour les partenaires B2B.",
)
async def search_b2b_results(
    examen_id: uuid.UUID,
    numero_pv: str,
    jury: str | None = None,
    api_key: ApiKey = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_db),
) -> list[ResultatPublicOut]:
    await _appliquer_quota(api_key, db)

    cle_cache = f"public:results:{examen_id}:{numero_pv}:{jury or ''}"
    cache = await cache_get(cle_cache)
    if cache is not None:
        return [ResultatPublicOut.model_validate(item) for item in cache]

    query = (
        select(Resultat)
        .join(Examen, Resultat.examen_id == Examen.id)
        .where(
            Examen.statut == StatutExamen.PUBLISHED,
            Resultat.examen_id == examen_id,
            Resultat.numero_pv == numero_pv,
        )
    )
    if jury is not None:
        query = query.where(Resultat.jury == jury)

    resultats_bd = (await db.execute(query)).scalars().all()
    if not resultats_bd:
        raise HTTPException(status_code=404, detail="Aucun résultat trouvé")

    resultats = [ResultatPublicOut.model_validate(r) for r in resultats_bd]
    await cache_set(
        cle_cache, [r.model_dump(mode="json") for r in resultats], settings.cache_ttl_seconds
    )
    return resultats
