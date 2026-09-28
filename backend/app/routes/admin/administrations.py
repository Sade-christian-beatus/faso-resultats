import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete
from app.core.deps import get_current_super_admin
from app.core.security import hash_password
from app.database import get_db
from app.models import ActionAuditLog, Administration, StatutAdministration, Utilisateur
from app.routes.public.results import CLE_CACHE_ADMINISTRATIONS, CLE_CACHE_EXAMENS
from app.schemas.administration import (
    AdministrationCreate,
    AdministrationOut,
    AdministrationUpdate,
    UtilisateurInitialCreate,
)
from app.schemas.auth import UtilisateurOut
from app.services.audit_service import journaliser_audit
from app.services.candidat.purge_service import marquer_candidatures_administration_resiliee

router = APIRouter(prefix="/api/v1/admin/administrations", tags=["super-admin"])


async def _get_administration_ou_404(
    administration_id: uuid.UUID, db: AsyncSession
) -> Administration:
    administration = await db.get(Administration, administration_id)
    if administration is None:
        raise HTTPException(status_code=404, detail="Administration introuvable")
    return administration


@router.post(
    "",
    response_model=AdministrationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une administration cliente (tenant)",
    description="Réservé aux comptes SUPER_ADMIN plateforme. Onboarding d'une nouvelle "
    "administration cliente — voir POST /{id}/utilisateurs pour créer son premier compte.",
)
async def create_administration(
    request: Request,
    payload: AdministrationCreate,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Administration:
    existante = await db.execute(select(Administration).where(Administration.code == payload.code))
    if existante.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Une administration avec le code '{payload.code}' existe déjà",
        )

    administration = Administration(**payload.model_dump())
    db.add(administration)
    await db.flush()
    await journaliser_audit(
        db,
        utilisateur_id=super_admin.id,
        administration_id=administration.id,
        action=ActionAuditLog.CREATE_ADMINISTRATION,
        request=request,
        details={"code": administration.code},
    )
    await db.commit()
    await db.refresh(administration)
    return administration


@router.get(
    "",
    response_model=list[AdministrationOut],
    summary="Lister les administrations clientes",
    description="Réservé aux comptes SUPER_ADMIN plateforme.",
)
async def list_administrations(
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> list[Administration]:
    result = await db.execute(select(Administration).order_by(Administration.created_at.desc()))
    return list(result.scalars().all())


@router.get(
    "/{administration_id}",
    response_model=AdministrationOut,
    summary="Détail d'une administration cliente",
    description="Réservé aux comptes SUPER_ADMIN plateforme.",
)
async def get_administration(
    administration_id: uuid.UUID,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Administration:
    return await _get_administration_ou_404(administration_id, db)


@router.patch(
    "/{administration_id}",
    response_model=AdministrationOut,
    summary="Modifier une administration cliente",
    description="Réservé aux comptes SUPER_ADMIN plateforme. Utilisé notamment pour "
    "suspendre (SUSPENDU) ou résilier (RESILIE) un tenant.",
)
async def update_administration(
    request: Request,
    administration_id: uuid.UUID,
    payload: AdministrationUpdate,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Administration:
    administration = await _get_administration_ou_404(administration_id, db)
    statut_avant = administration.statut

    updates = payload.model_dump(exclude_unset=True)
    for champ, valeur in updates.items():
        setattr(administration, champ, valeur)

    if (
        statut_avant != StatutAdministration.RESILIE
        and administration.statut == StatutAdministration.RESILIE
    ):
        # Candidatures orphelines (docs/PROFIL_CANDIDAT_UNIFIE.md § 7) : marquées
        # immédiatement, purgées après 6 mois par le script purge_candidats.py.
        await marquer_candidatures_administration_resiliee(db, administration.id)

    await journaliser_audit(
        db,
        utilisateur_id=super_admin.id,
        administration_id=administration.id,
        action=ActionAuditLog.UPDATE_ADMINISTRATION,
        request=request,
        details={"champs_modifies": list(updates.keys())},
    )
    await db.commit()
    await db.refresh(administration)

    if administration.statut != statut_avant:
        # Public/B2B visibility depends on the status (STATUTS_ADMINISTRATION_VISIBLES):
        # drop the cached lists so a suspension takes effect immediately. Cached result
        # lookups (per PV number, keys not enumerable) expire on their own within
        # cache_ttl_seconds.
        await cache_delete(CLE_CACHE_EXAMENS)
        await cache_delete(CLE_CACHE_ADMINISTRATIONS)
    return administration


@router.post(
    "/{administration_id}/utilisateurs",
    response_model=UtilisateurOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un utilisateur pour cette administration",
    description="Réservé aux comptes SUPER_ADMIN plateforme. Typiquement utilisé pour "
    "provisionner le premier compte ADMIN_ADMINISTRATION d'un nouveau tenant.",
)
async def create_utilisateur_administration(
    request: Request,
    administration_id: uuid.UUID,
    payload: UtilisateurInitialCreate,
    super_admin: Utilisateur = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Utilisateur:
    administration = await _get_administration_ou_404(administration_id, db)

    existant = await db.execute(select(Utilisateur).where(Utilisateur.email == payload.email))
    if existant.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un utilisateur avec l'email '{payload.email}' existe déjà",
        )

    utilisateur = Utilisateur(
        administration_id=administration.id,
        email=payload.email,
        mot_de_passe_hash=hash_password(payload.password),
        nom_complet=payload.nom_complet,
        telephone=payload.telephone,
        role=payload.role,
    )
    db.add(utilisateur)
    await db.flush()
    await journaliser_audit(
        db,
        utilisateur_id=super_admin.id,
        administration_id=administration.id,
        action=ActionAuditLog.CREATE_UTILISATEUR,
        request=request,
        details={"utilisateur_id": str(utilisateur.id), "role": payload.role.value},
    )
    await db.commit()
    await db.refresh(utilisateur)
    return utilisateur
