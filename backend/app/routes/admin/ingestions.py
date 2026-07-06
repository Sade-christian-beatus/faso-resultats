import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import get_settings
from app.core.deps import get_current_administration, get_current_utilisateur
from app.database import get_db
from app.models import Administration, Examen, Ingestion, StatutIngestion, TypeFichier, Utilisateur
from app.schemas.ingestion import CorrectionRequest, IngestionOut, IngestionPreviewOut, LigneApercu
from app.services.ingestion.dispatch import parser_fichier
from app.services.ingestion.publication import construire_resultats
from app.services.ingestion.template import construire_modele_excel

router = APIRouter(prefix="/api/v1/admin/ingestions", tags=["admin-ingestions"])
settings = get_settings()

_EXTENSIONS_AUTORISEES = {
    TypeFichier.EXCEL: {".xlsx", ".xls"},
    TypeFichier.PDF: {".pdf"},
    TypeFichier.PDF_OCR: {".pdf"},
}


async def _get_ingestion_ou_404(
    ingestion_id: uuid.UUID, administration: Administration, db: AsyncSession
) -> Ingestion:
    """Filtre systématiquement par administration : une ingestion d'un autre tenant
    renvoie 404 comme si elle n'existait pas, pour ne jamais confirmer son existence."""
    ingestion = await db.get(Ingestion, ingestion_id)
    if ingestion is None or ingestion.administration_id != administration.id:
        raise HTTPException(status_code=404, detail="Ingestion introuvable")
    return ingestion


def _vers_preview(ingestion: Ingestion) -> IngestionPreviewOut:
    return IngestionPreviewOut(
        **IngestionOut.model_validate(ingestion).model_dump(),
        lignes=[LigneApercu(**ligne) for ligne in ingestion.apercu_donnees],
    )


@router.post(
    "",
    response_model=IngestionPreviewOut,
    status_code=status.HTTP_201_CREATED,
    summary="Uploader un fichier de résultats",
    description="Upload puis parsing immédiat (aperçu). Rien n'est publié tant que "
    "POST /publish n'est pas appelé explicitement.",
)
async def upload_ingestion(
    examen_id: uuid.UUID = Form(...),
    type_fichier: TypeFichier = Form(...),
    file: UploadFile = File(...),
    decision_par_defaut: str | None = Form(
        None,
        description="Appliquée à toute ligne sans décision propre (ex. listes "
        "d'admissibilité à un concours, où la décision vaut pour tout le document).",
    ),
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> IngestionPreviewOut:
    examen = await db.get(Examen, examen_id)
    if examen is None or examen.administration_id != administration.id:
        raise HTTPException(status_code=404, detail="Examen introuvable")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in _EXTENSIONS_AUTORISEES[type_fichier]:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Extension '{extension}' incompatible avec le type de fichier "
                f"{type_fichier.value}"
            ),
        )

    contenu = await file.read()
    taille_max = settings.max_upload_size_mb * 1024 * 1024
    if len(contenu) > taille_max:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (max {settings.max_upload_size_mb} Mo)",
        )

    ingestion_id = uuid.uuid4()
    dossier_examen = Path(settings.uploads_dir) / str(examen_id)
    dossier_examen.mkdir(parents=True, exist_ok=True)
    chemin_fichier = dossier_examen / f"{ingestion_id}{extension}"
    chemin_fichier.write_bytes(contenu)

    resultat_parsing = parser_fichier(chemin_fichier, type_fichier, decision_par_defaut)

    ingestion = Ingestion(
        id=ingestion_id,
        administration_id=administration.id,
        examen_id=examen_id,
        admin_id=current_utilisateur.id,
        nom_fichier=file.filename or chemin_fichier.name,
        chemin_fichier=str(chemin_fichier),
        type_fichier=type_fichier,
        statut=StatutIngestion.PREVISUALISATION,
        nombre_lignes_detectees=resultat_parsing.nombre_lignes,
        nombre_erreurs=resultat_parsing.nombre_erreurs,
        erreurs_fichier=resultat_parsing.erreurs_fichier,
        apercu_donnees=[ligne.as_dict() for ligne in resultat_parsing.lignes],
    )
    db.add(ingestion)
    await db.commit()
    await db.refresh(ingestion)
    return _vers_preview(ingestion)


@router.get(
    "/template",
    summary="Télécharger le modèle Excel d'import",
    description="Fichier .xlsx avec les en-têtes exactes reconnues par le parser, pour "
    "une administration qui n'a pas encore de fichier dans un format compatible.",
)
async def download_template(
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
) -> Response:
    return Response(
        content=construire_modele_excel(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=modele-import-resultats.xlsx"},
    )


@router.get(
    "",
    response_model=list[IngestionOut],
    summary="Lister les ingestions",
    description="Vue admin des ingestions de l'administration de l'utilisateur connecté, "
    "filtrable par examen.",
)
async def list_ingestions(
    examen_id: uuid.UUID | None = None,
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> list[Ingestion]:
    query = (
        select(Ingestion)
        .where(Ingestion.administration_id == administration.id)
        .order_by(Ingestion.created_at.desc())
    )
    if examen_id is not None:
        query = query.where(Ingestion.examen_id == examen_id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/{ingestion_id}",
    response_model=IngestionPreviewOut,
    summary="Détail d'une ingestion",
    description="Renvoie l'ingestion avec l'aperçu complet des lignes extraites, pour "
    "prévisualisation et correction.",
)
async def get_ingestion(
    ingestion_id: uuid.UUID,
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> IngestionPreviewOut:
    ingestion = await _get_ingestion_ou_404(ingestion_id, administration, db)
    return _vers_preview(ingestion)


@router.patch(
    "/{ingestion_id}",
    response_model=IngestionPreviewOut,
    summary="Corriger les lignes d'une ingestion",
    description="Remplace l'aperçu des lignes par la version corrigée manuellement par "
    "l'admin. Uniquement possible tant que l'ingestion n'est pas publiée ni rejetée.",
)
async def correct_ingestion(
    ingestion_id: uuid.UUID,
    payload: CorrectionRequest,
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> IngestionPreviewOut:
    ingestion = await _get_ingestion_ou_404(ingestion_id, administration, db)
    if ingestion.statut != StatutIngestion.PREVISUALISATION:
        raise HTTPException(
            status_code=409,
            detail="Cette ingestion n'est plus modifiable (déjà publiée ou rejetée)",
        )

    ingestion.apercu_donnees = [ligne.model_dump() for ligne in payload.lignes]
    ingestion.nombre_lignes_detectees = len(payload.lignes)
    ingestion.nombre_erreurs = sum(1 for ligne in payload.lignes if ligne.erreurs)
    await db.commit()
    await db.refresh(ingestion)
    return _vers_preview(ingestion)


@router.post(
    "/{ingestion_id}/publish",
    response_model=IngestionOut,
    summary="Publier une ingestion",
    description="Transforme l'aperçu validé en résultats officiels. Bloqué si des lignes "
    "portent encore des erreurs (validation humaine obligatoire avant publication). "
    "Les résultats restent invisibles côté public tant que l'examen associé n'est pas "
    "lui-même publié (permet de préparer plusieurs jurys avant une mise en ligne "
    "coordonnée, ex. jour de proclamation du BAC).",
)
async def publish_ingestion(
    ingestion_id: uuid.UUID,
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> Ingestion:
    ingestion = await _get_ingestion_ou_404(ingestion_id, administration, db)
    if ingestion.statut != StatutIngestion.PREVISUALISATION:
        raise HTTPException(
            status_code=409, detail="Cette ingestion n'est pas en attente de publication"
        )
    if ingestion.nombre_erreurs > 0:
        raise HTTPException(
            status_code=400,
            detail="Des lignes contiennent encore des erreurs : corrigez-les avant de publier",
        )
    if not ingestion.apercu_donnees:
        raise HTTPException(status_code=400, detail="Aucune ligne à publier")

    for resultat in construire_resultats(ingestion):
        db.add(resultat)

    ingestion.statut = StatutIngestion.PUBLIEE
    ingestion.publiee_at = func.now()
    await db.commit()
    await db.refresh(ingestion)
    return ingestion


@router.post(
    "/{ingestion_id}/reject",
    response_model=IngestionOut,
    summary="Rejeter une ingestion",
    description="Écarte l'ingestion sans créer de résultats (ex : mauvais fichier importé).",
)
async def reject_ingestion(
    ingestion_id: uuid.UUID,
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> Ingestion:
    ingestion = await _get_ingestion_ou_404(ingestion_id, administration, db)
    if ingestion.statut != StatutIngestion.PREVISUALISATION:
        raise HTTPException(status_code=409, detail="Cette ingestion n'est pas en attente")

    ingestion.statut = StatutIngestion.REJETEE
    await db.commit()
    await db.refresh(ingestion)
    return ingestion
