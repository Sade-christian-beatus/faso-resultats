import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_super_admin
from app.core.security import generer_cle_api, hash_cle_api, prefixe_affichable
from app.database import get_db
from app.models import ActionAuditLog, ApiKey, Partenaire, StatutApiKey, Utilisateur
from app.schemas.partenaire import (
    ApiKeyCreate,
    ApiKeyCreeeOut,
    ApiKeyOut,
    PartenaireCreate,
    PartenaireOut,
    PartenaireUpdate,
)
from app.services.audit_service import journaliser_audit

router = APIRouter(prefix="/api/v1/admin/partenaires", tags=["super-admin"])


async def _get_partenaire_ou_404(partenaire_id: uuid.UUID, db: AsyncSession) -> Partenaire:
    partenaire = await db.get(Partenaire, partenaire_id)
    if partenaire is None:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    return partenaire


async def _get_api_key_ou_404(
    partenaire_id: uuid.UUID, api_key_id: uuid.UUID, db: AsyncSession
) -> ApiKey:
    api_key = await db.get(ApiKey, api_key_id)
    if api_key is None or api_key.partenaire_id != partenaire_id:
        raise HTTPException(status_code=404, detail="Clé API introuvable")
    return api_key


@router.post(
    "",
    response_model=PartenaireOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un partenaire B2B",
    description="Réservé aux comptes SUPER_ADMIN plateforme. Un partenaire (école "
    "privée, média, ONG...) est transversal aux administrations clientes — voir "
    "POST /{id}/api-keys pour lui émettre une clé d'accès à l'API.",
)
async def create_partenaire(
    request: Request,
    payload: PartenaireCreate,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Partenaire:
    partenaire = Partenaire(**payload.model_dump())
    db.add(partenaire)
    await db.flush()
    await journaliser_audit(
        db,
        utilisateur_id=super_admin.id,
        administration_id=None,
        action=ActionAuditLog.CREATE_PARTENAIRE,
        request=request,
        details={"partenaire_id": str(partenaire.id)},
    )
    await db.commit()
    await db.refresh(partenaire)
    return partenaire


@router.get(
    "",
    response_model=list[PartenaireOut],
    summary="Lister les partenaires B2B",
    description="Réservé aux comptes SUPER_ADMIN plateforme.",
)
async def list_partenaires(
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[Partenaire]:
    result = await db.execute(select(Partenaire).order_by(Partenaire.created_at.desc()))
    return list(result.scalars().all())


@router.get(
    "/{partenaire_id}",
    response_model=PartenaireOut,
    summary="Détail d'un partenaire B2B",
    description="Réservé aux comptes SUPER_ADMIN plateforme.",
)
async def get_partenaire(
    partenaire_id: uuid.UUID,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Partenaire:
    return await _get_partenaire_ou_404(partenaire_id, db)


@router.patch(
    "/{partenaire_id}",
    response_model=PartenaireOut,
    summary="Modifier un partenaire B2B",
    description="Réservé aux comptes SUPER_ADMIN plateforme. Utilisé notamment pour "
    "suspendre un partenaire (SUSPENDU) sans toucher à ses clés individuellement.",
)
async def update_partenaire(
    request: Request,
    partenaire_id: uuid.UUID,
    payload: PartenaireUpdate,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Partenaire:
    partenaire = await _get_partenaire_ou_404(partenaire_id, db)
    updates = payload.model_dump(exclude_unset=True)
    for champ, valeur in updates.items():
        setattr(partenaire, champ, valeur)

    await journaliser_audit(
        db,
        utilisateur_id=super_admin.id,
        administration_id=None,
        action=ActionAuditLog.UPDATE_PARTENAIRE,
        request=request,
        details={"partenaire_id": str(partenaire.id), "champs_modifies": list(updates.keys())},
    )
    await db.commit()
    await db.refresh(partenaire)
    return partenaire


@router.post(
    "/{partenaire_id}/api-keys",
    response_model=ApiKeyCreeeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Émettre une clé API pour ce partenaire",
    description="Réservé aux comptes SUPER_ADMIN plateforme. La clé en clair n'est "
    "renvoyée qu'une seule fois, dans cette réponse — elle n'est jamais récupérable "
    "ensuite (seul son hash est stocké).",
)
async def create_api_key(
    request: Request,
    partenaire_id: uuid.UUID,
    payload: ApiKeyCreate,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreeeOut:
    await _get_partenaire_ou_404(partenaire_id, db)

    cle = generer_cle_api()
    api_key = ApiKey(
        partenaire_id=partenaire_id,
        prefixe=prefixe_affichable(cle),
        cle_hash=hash_cle_api(cle),
        tier=payload.tier,
        quota_quotidien=payload.quota_quotidien,
    )
    db.add(api_key)
    await db.flush()
    await journaliser_audit(
        db,
        utilisateur_id=super_admin.id,
        administration_id=None,
        action=ActionAuditLog.CREATE_API_KEY,
        request=request,
        details={"partenaire_id": str(partenaire_id), "api_key_id": str(api_key.id)},
    )
    await db.commit()
    await db.refresh(api_key)
    return ApiKeyCreeeOut(**ApiKeyOut.model_validate(api_key).model_dump(), cle=cle)


@router.get(
    "/{partenaire_id}/api-keys",
    response_model=list[ApiKeyOut],
    summary="Lister les clés API d'un partenaire",
    description="Réservé aux comptes SUPER_ADMIN plateforme. Ne renvoie jamais la "
    "clé en clair, uniquement son préfixe identifiant.",
)
async def list_api_keys(
    partenaire_id: uuid.UUID,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKey]:
    await _get_partenaire_ou_404(partenaire_id, db)
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.partenaire_id == partenaire_id)
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


@router.post(
    "/{partenaire_id}/api-keys/{api_key_id}/revoke",
    response_model=ApiKeyOut,
    summary="Révoquer une clé API",
    description="Réservé aux comptes SUPER_ADMIN plateforme. Irréversible : émettre "
    "une nouvelle clé si le partenaire a besoin d'un nouvel accès.",
)
async def revoke_api_key(
    request: Request,
    partenaire_id: uuid.UUID,
    api_key_id: uuid.UUID,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    api_key = await _get_api_key_ou_404(partenaire_id, api_key_id, db)
    api_key.statut = StatutApiKey.REVOQUEE

    await journaliser_audit(
        db,
        utilisateur_id=super_admin.id,
        administration_id=None,
        action=ActionAuditLog.REVOKE_API_KEY,
        request=request,
        details={"partenaire_id": str(partenaire_id), "api_key_id": str(api_key.id)},
    )
    await db.commit()
    await db.refresh(api_key)
    return api_key
