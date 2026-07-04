import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.database import get_db
from app.models import Examen, StatutExamen
from app.schemas.examen import ExamenCreate, ExamenOut

router = APIRouter(
    prefix="/api/v1/admin/exams",
    tags=["admin-exams"],
    dependencies=[Depends(get_current_admin)],
)


@router.post(
    "",
    response_model=ExamenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un examen",
    description="Crée un examen en statut DRAFT (jamais visible côté public tant qu'il n'est "
    "pas publié explicitement).",
)
async def create_exam(payload: ExamenCreate, db: AsyncSession = Depends(get_db)) -> Examen:
    examen = Examen(
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
    description="Liste tous les examens quel que soit leur statut (vue admin).",
)
async def list_exams(db: AsyncSession = Depends(get_db)) -> list[Examen]:
    result = await db.execute(select(Examen).order_by(Examen.annee.desc()))
    return list(result.scalars().all())


@router.post(
    "/{exam_id}/publish",
    response_model=ExamenOut,
    summary="Publier un examen",
    description="Rend l'examen visible côté public. Les résultats déjà publiés via une "
    "ingestion deviennent alors consultables.",
)
async def publish_exam(exam_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Examen:
    examen = await db.get(Examen, exam_id)
    if examen is None:
        raise HTTPException(status_code=404, detail="Examen introuvable")

    examen.statut = StatutExamen.PUBLISHED
    await db.commit()
    await db.refresh(examen)
    return examen
