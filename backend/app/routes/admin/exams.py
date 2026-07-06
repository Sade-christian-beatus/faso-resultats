import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_administration
from app.database import get_db
from app.models import Administration, Examen, StatutExamen
from app.schemas.examen import ExamenCreate, ExamenOut
from app.services.candidat.matching_service import MatchingService

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
    payload: ExamenCreate,
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
        phases_publication=payload.phases_publication,
    )
    db.add(examen)
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
    exam_id: uuid.UUID,
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> Examen:
    examen = await _get_exam_ou_404(exam_id, administration, db)

    examen.statut = StatutExamen.PUBLISHED
    # Rapproche les candidatures plateforme en attente de ce résultat désormais publié,
    # et notifie les candidats concernés (docs/PROFIL_CANDIDAT_UNIFIE.md § 4.5, § 6).
    await MatchingService(db).traiter_publication_examen(examen)
    await db.commit()
    await db.refresh(examen)
    return examen
