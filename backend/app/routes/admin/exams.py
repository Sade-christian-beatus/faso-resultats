import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_administration, get_current_utilisateur
from app.database import get_db
from app.models import (
    ActionAuditLog,
    Administration,
    Examen,
    Ingestion,
    PhasePublication,
    StatutExamen,
    StatutIngestion,
    Utilisateur,
)
from app.schemas.examen import ExamenCreate, ExamenOut
from app.services.audit_service import journaliser_audit
from app.services.candidat.matching_service import MatchingService
from app.services.phases import ErreurPhase, verifier_cloturable

router = APIRouter(prefix="/api/v1/admin/exams", tags=["admin-exams"])


async def _get_exam_ou_404(
    exam_id: uuid.UUID, administration: Administration, db: AsyncSession
) -> Examen:
    """Filtre systématiquement par administration : un examen d'un autre tenant
    renvoie 404 comme s'il n'existait pas, pour ne jamais confirmer son existence."""
    examen = await db.get(Examen, exam_id)
    if examen is None or examen.administration_id != administration.id:
        raise HTTPException(status_code=404, detail="Examen introuvable")
    return examen


@router.post(
    "",
    response_model=ExamenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un examen",
    description="Crée un examen en statut DRAFT (jamais visible côté public tant qu'il n'est "
    "pas publié explicitement), rattaché à l'administration de l'utilisateur connecté.",
)
async def create_exam(
    request: Request,
    payload: ExamenCreate,
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> Examen:
    examen = Examen(
        administration_id=administration.id,
        type_examen=payload.type_examen,
        annee=payload.annee,
        libelle=payload.libelle,
        categorie=payload.categorie,
        serie=payload.serie,
        ministere_tutelle=payload.ministere_tutelle,
        source_donnees=payload.source_donnees,
        partenariat_officiel=payload.partenariat_officiel,
        phases_publication=[phase.value for phase in payload.phases_publication],
    )
    db.add(examen)
    await db.flush()
    await journaliser_audit(
        db,
        utilisateur_id=current_utilisateur.id,
        administration_id=administration.id,
        action=ActionAuditLog.CREATE_EXAMEN,
        request=request,
        details={"examen_id": str(examen.id)},
    )
    await db.commit()
    await db.refresh(examen)
    return examen


@router.get(
    "",
    response_model=list[ExamenOut],
    summary="Lister les examens",
    description="Liste les examens de l'administration de l'utilisateur connecté, quel "
    "que soit leur statut.",
)
async def list_exams(
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> list[Examen]:
    result = await db.execute(
        select(Examen)
        .where(Examen.administration_id == administration.id)
        .order_by(Examen.annee.desc())
    )
    return list(result.scalars().all())


@router.post(
    "/{exam_id}/publish",
    response_model=ExamenOut,
    summary="Publier un examen",
    description="Rend l'examen visible côté public. Les résultats déjà publiés via une "
    "ingestion deviennent alors consultables.",
)
async def publish_exam(
    request: Request,
    exam_id: uuid.UUID,
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> Examen:
    examen = await _get_exam_ou_404(exam_id, administration, db)

    examen.statut = StatutExamen.PUBLISHED
    # Rapproche les candidatures plateforme en attente de ce résultat désormais publié,
    # et notifie les candidats concernés (docs/PROFIL_CANDIDAT_UNIFIE.md § 4.5, § 6).
    await MatchingService(db).traiter_publication_examen(examen)
    await journaliser_audit(
        db,
        utilisateur_id=current_utilisateur.id,
        administration_id=administration.id,
        action=ActionAuditLog.PUBLISH_EXAMEN,
        request=request,
        details={"examen_id": str(examen.id)},
    )
    await db.commit()
    await db.refresh(examen)
    return examen


@router.post(
    "/{exam_id}/phases/{phase}/close",
    response_model=ExamenOut,
    summary="Clôturer une phase de publication",
    description="Déclare que toutes les listes de cette phase sont publiées (concours à "
    "plusieurs phases). Irréversible : plus aucune liste ne peut être publiée pour cette "
    "phase, la phase suivante devient publiable, et un candidat de la phase précédente "
    "absent des listes de cette phase est informé qu'il n'y figure pas.",
)
async def close_phase(
    request: Request,
    exam_id: uuid.UUID,
    phase: PhasePublication,
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> Examen:
    examen = await _get_exam_ou_404(exam_id, administration, db)

    nombre_par_statut = dict(
        (
            await db.execute(
                select(Ingestion.statut, func.count())
                .where(Ingestion.examen_id == examen.id, Ingestion.phase == phase)
                .group_by(Ingestion.statut)
            )
        ).all()
    )
    try:
        verifier_cloturable(
            examen,
            phase,
            nombre_listes_publiees=nombre_par_statut.get(StatutIngestion.PUBLIEE, 0),
            nombre_listes_en_attente=nombre_par_statut.get(StatutIngestion.PREVISUALISATION, 0),
        )
    except ErreurPhase as erreur:
        raise HTTPException(status_code=409, detail=str(erreur)) from erreur

    # Reassigned, not mutated in place: plain JSON columns do not track mutations.
    examen.phases_cloturees = [*(examen.phases_cloturees or []), phase.value]
    if examen.statut == StatutExamen.PUBLISHED:
        await MatchingService(db).traiter_cloture_phase(examen, phase)
    await journaliser_audit(
        db,
        utilisateur_id=current_utilisateur.id,
        administration_id=administration.id,
        action=ActionAuditLog.CLOSE_PHASE,
        request=request,
        details={"examen_id": str(examen.id), "phase": phase.value},
    )
    await db.commit()
    await db.refresh(examen)
    return examen
