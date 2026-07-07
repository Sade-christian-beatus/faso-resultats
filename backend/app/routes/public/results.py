import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.cache import cache_get, cache_set
from app.core.rate_limit import limiter
from app.database import get_db
from app.models import Examen, Resultat, StatutExamen
from app.schemas.public import DroitsCandidatOut, ExamenPublicOut, ResultatPublicOut

router = APIRouter(prefix="/api/v1/public", tags=["public"])
settings = get_settings()


@router.get(
    "/exams",
    response_model=list[ExamenPublicOut],
    summary="Lister les examens publiés",
    description="Examens visibles publiquement (statut PUBLISHED uniquement). Résultat mis en "
    "cache.",
)
@limiter.limit(settings.rate_limit_public)
async def list_public_exams(
    request: Request, db: AsyncSession = Depends(get_db)
) -> list[ExamenPublicOut]:
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
    summary="Consulter un résultat",
    description="Recherche par numéro de PV (et jury en option pour désambiguïser). Ne renvoie "
    "que les résultats appartenant à un examen publié.",
)
@limiter.limit(settings.rate_limit_public)
async def search_public_results(
    request: Request,
    examen_id: uuid.UUID,
    numero_pv: str,
    jury: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ResultatPublicOut]:
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


@router.get(
    "/droits-candidat",
    response_model=DroitsCandidatOut,
    summary="Exercer ses droits sur le profil candidat",
    description="Canal de contact dédié aux demandes d'exercice de droits qui ne "
    "passent pas par les endpoints candidat en libre-service (GET/PATCH/DELETE "
    "/api/v1/candidat/me, GET /api/v1/candidat/me/export) — par exemple une demande "
    "formulée par un tiers, ou une correction d'identité (CNIB, nom, date de "
    "naissance), volontairement non modifiable en libre-service.",
)
@limiter.limit(settings.rate_limit_public)
async def droits_candidat(request: Request) -> DroitsCandidatOut:
    return DroitsCandidatOut(
        contact_dpo=settings.candidat_dpo_contact_email,
        droits=[
            "Droit d'accès : GET /api/v1/candidat/me",
            "Droit à la portabilité : GET /api/v1/candidat/me/export",
            "Droit de rectification (préférences, email) : PATCH /api/v1/candidat/me",
            "Droit de rectification (identité : CNIB, nom, date de naissance) : "
            "contacter le DPO",
            "Droit à l'effacement : DELETE /api/v1/candidat/me",
        ],
        delai_reponse_indicatif="Sous 30 jours",
    )
