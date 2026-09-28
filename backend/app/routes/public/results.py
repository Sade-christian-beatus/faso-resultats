import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.cache import cache_get, cache_set
from app.core.rate_limit import limiter
from app.database import get_db
from app.models import (
    STATUTS_ADMINISTRATION_VISIBLES,
    Administration,
    Examen,
    Ingestion,
    Resultat,
    StatutExamen,
    StatutIngestion,
)
from app.schemas.public import (
    AdministrationPublicOut,
    DroitsCandidatOut,
    EtapeParcoursOut,
    ExamenPublicOut,
    ParcoursCandidatOut,
    ResultatPublicOut,
)
from app.services.phases import construire_parcours

router = APIRouter(prefix="/api/v1/public", tags=["public"])
settings = get_settings()

# Cache keys invalidated when an administration's status changes
# (routes/admin/administrations.py). Shared with the B2B routes.
CLE_CACHE_ADMINISTRATIONS = "public:administrations"
CLE_CACHE_EXAMENS = "public:exams"


@router.get(
    "/administrations",
    response_model=list[AdministrationPublicOut],
    summary="Lister les administrations clientes actives",
    description="Administrations visibles publiquement (ACTIF ou PILOTE uniquement, "
    "comme pour l'ajout de candidature). Résultat mis en cache.",
)
@limiter.limit(settings.rate_limit_public)
async def list_public_administrations(
    request: Request, db: AsyncSession = Depends(get_db)
) -> list[AdministrationPublicOut]:
    cle_cache = CLE_CACHE_ADMINISTRATIONS
    cache = await cache_get(cle_cache)
    if cache is not None:
        return [AdministrationPublicOut.model_validate(item) for item in cache]

    result = await db.execute(
        select(Administration)
        .where(Administration.statut.in_(STATUTS_ADMINISTRATION_VISIBLES))
        .order_by(Administration.nom_officiel)
    )
    administrations = [AdministrationPublicOut.model_validate(a) for a in result.scalars().all()]
    await cache_set(
        cle_cache,
        [a.model_dump(mode="json") for a in administrations],
        settings.cache_ttl_seconds,
    )
    return administrations


@router.get(
    "/exams",
    response_model=list[ExamenPublicOut],
    summary="Lister les examens publiés",
    description="Examens visibles publiquement (statut PUBLISHED uniquement, administration "
    "ACTIF ou PILOTE). Résultat mis en cache.",
)
@limiter.limit(settings.rate_limit_public)
async def list_public_exams(
    request: Request, db: AsyncSession = Depends(get_db)
) -> list[ExamenPublicOut]:
    cle_cache = CLE_CACHE_EXAMENS
    cache = await cache_get(cle_cache)
    if cache is not None:
        return [ExamenPublicOut.model_validate(item) for item in cache]

    result = await db.execute(
        select(Examen)
        .join(Administration, Examen.administration_id == Administration.id)
        .where(
            Examen.statut == StatutExamen.PUBLISHED,
            Administration.statut.in_(STATUTS_ADMINISTRATION_VISIBLES),
        )
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
    "que les résultats appartenant à un examen publié d'une administration ACTIF ou PILOTE.",
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
        .join(Administration, Examen.administration_id == Administration.id)
        .where(
            Examen.statut == StatutExamen.PUBLISHED,
            Administration.statut.in_(STATUTS_ADMINISTRATION_VISIBLES),
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
    "/results/progress",
    response_model=list[ParcoursCandidatOut],
    summary="Suivre son parcours phase par phase",
    description="Pour les concours publiés en plusieurs phases (épreuves sportives, "
    "admissibilité, admission définitive) : situation du candidat à chaque phase — "
    "résultat, publication en cours, ne figure pas sur la liste (uniquement une fois la "
    "phase clôturée par l'administration), à venir. Même recherche et mêmes filtres que "
    "GET /results ; fonctionne aussi pour un examen à publication unique.",
)
@limiter.limit(settings.rate_limit_public)
async def search_public_progress(
    request: Request,
    examen_id: uuid.UUID,
    numero_pv: str,
    jury: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ParcoursCandidatOut]:
    cle_cache = f"public:progress:{examen_id}:{numero_pv}:{jury or ''}"
    cache = await cache_get(cle_cache)
    if cache is not None:
        return [ParcoursCandidatOut.model_validate(item) for item in cache]

    examen = (
        await db.execute(
            select(Examen)
            .join(Administration, Examen.administration_id == Administration.id)
            .where(
                Examen.id == examen_id,
                Examen.statut == StatutExamen.PUBLISHED,
                Administration.statut.in_(STATUTS_ADMINISTRATION_VISIBLES),
            )
        )
    ).scalar_one_or_none()
    if examen is None:
        raise HTTPException(status_code=404, detail="Aucun résultat trouvé")

    query = select(Resultat).where(Resultat.examen_id == examen.id, Resultat.numero_pv == numero_pv)
    if jury is not None:
        query = query.where(Resultat.jury == jury)
    resultats = (await db.execute(query)).scalars().all()
    if not resultats:
        raise HTTPException(status_code=404, detail="Aucun résultat trouvé")

    phases_avec_listes = set(
        (
            await db.execute(
                select(Ingestion.phase)
                .where(
                    Ingestion.examen_id == examen.id,
                    Ingestion.statut == StatutIngestion.PUBLIEE,
                )
                .distinct()
            )
        )
        .scalars()
        .all()
    )
    par_candidat: dict[tuple[str, str], list[Resultat]] = {}
    for resultat in resultats:
        par_candidat.setdefault((resultat.numero_pv, resultat.jury), []).append(resultat)

    parcours = [
        ParcoursCandidatOut(
            numero_pv=pv,
            jury=jury_candidat,
            etapes=[
                EtapeParcoursOut(
                    phase=etape.phase,
                    statut_phase=etape.statut_phase,
                    situation=etape.situation,
                    resultat=(
                        ResultatPublicOut.model_validate(etape.resultat) if etape.resultat else None
                    ),
                )
                for etape in construire_parcours(examen, lignes, phases_avec_listes)
            ],
        )
        for (pv, jury_candidat), lignes in sorted(par_candidat.items())
    ]
    await cache_set(
        cle_cache, [p.model_dump(mode="json") for p in parcours], settings.cache_ttl_seconds
    )
    return parcours


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
