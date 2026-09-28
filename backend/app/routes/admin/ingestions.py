import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import get_settings
from app.core.deps import get_current_administration, get_current_utilisateur
from app.database import get_db
from app.models import (
    ActionAuditLog,
    Administration,
    Examen,
    Ingestion,
    PhasePublication,
    Resultat,
    StatutExamen,
    StatutIngestion,
    TypeFichier,
    Utilisateur,
)
from app.schemas.ingestion import CorrectionRequest, IngestionOut, IngestionPreviewOut, LigneApercu
from app.services.audit_service import journaliser_audit
from app.services.candidat.matching_service import MatchingService
from app.services.ingestion.dispatch import parser_fichier
from app.services.ingestion.normalizer import valider_ligne_normalisee
from app.services.ingestion.publication import construire_resultats
from app.services.ingestion.template import construire_modele_excel
from app.services.phases import ErreurPhase, phase_par_defaut, verifier_phase_ouverte

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
    request: Request,
    examen_id: uuid.UUID = Form(...),
    type_fichier: TypeFichier = Form(...),
    file: UploadFile = File(...),
    decision_par_defaut: str | None = Form(
        None,
        description="Appliquée à toute ligne sans décision propre (ex. listes "
        "d'admissibilité à un concours, où la décision vaut pour tout le document).",
    ),
    phase: PhasePublication | None = Form(
        None,
        description="Phase à laquelle appartient cette liste. Obligatoire pour un examen à "
        "plusieurs phases (concours paramilitaires) ; déduite sinon.",
    ),
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> IngestionPreviewOut:
    examen = await db.get(Examen, examen_id)
    if examen is None or examen.administration_id != administration.id:
        raise HTTPException(status_code=404, detail="Examen introuvable")

    phase = phase or phase_par_defaut(examen)
    if phase is None:
        raise HTTPException(
            status_code=422,
            detail="Cet examen comporte plusieurs phases : précisez à quelle phase "
            "appartient cette liste",
        )
    try:
        verifier_phase_ouverte(examen, phase)
    except ErreurPhase as erreur:
        raise HTTPException(status_code=409, detail=str(erreur)) from erreur

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
        phase=phase,
        nombre_lignes_detectees=resultat_parsing.nombre_lignes,
        nombre_erreurs=resultat_parsing.nombre_erreurs,
        erreurs_fichier=resultat_parsing.erreurs_fichier,
        apercu_donnees=[ligne.as_dict() for ligne in resultat_parsing.lignes],
    )
    db.add(ingestion)
    await journaliser_audit(
        db,
        utilisateur_id=current_utilisateur.id,
        administration_id=administration.id,
        action=ActionAuditLog.UPLOAD_INGESTION,
        request=request,
        details={"ingestion_id": str(ingestion.id), "examen_id": str(examen_id)},
    )
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
    request: Request,
    ingestion_id: uuid.UUID,
    payload: CorrectionRequest,
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> IngestionPreviewOut:
    ingestion = await _get_ingestion_ou_404(ingestion_id, administration, db)
    if ingestion.statut != StatutIngestion.PREVISUALISATION:
        raise HTTPException(
            status_code=409,
            detail="Cette ingestion n'est plus modifiable (déjà publiée ou rejetée)",
        )

    # La liste `erreurs` envoyée par le client n'est jamais fiable (bug/désync front,
    # payload manuel) : on revalide chaque ligne côté serveur à partir de ses données,
    # sans jamais faire confiance à ce que le client prétend avoir corrigé.
    lignes_revalidees = [
        LigneApercu(
            ligne=ligne.ligne,
            donnees=ligne.donnees,
            brut=ligne.brut,
            erreurs=valider_ligne_normalisee(ligne.donnees),
        )
        for ligne in payload.lignes
    ]

    ingestion.apercu_donnees = [ligne.model_dump() for ligne in lignes_revalidees]
    ingestion.nombre_lignes_detectees = len(lignes_revalidees)
    ingestion.nombre_erreurs = sum(1 for ligne in lignes_revalidees if ligne.erreurs)
    await journaliser_audit(
        db,
        utilisateur_id=current_utilisateur.id,
        administration_id=administration.id,
        action=ActionAuditLog.CORRECT_INGESTION,
        request=request,
        details={"ingestion_id": str(ingestion.id)},
    )
    await db.commit()
    await db.refresh(ingestion)
    return _vers_preview(ingestion)


async def _refuser_doublons(
    resultats: list[Resultat], examen: Examen, phase: PhasePublication, db: AsyncSession
) -> None:
    """A candidate (PV number + jury) has at most one result per phase. Report every
    conflict clearly instead of letting the unique index fail with a 500: typically the
    same list imported twice, or a list imported under the wrong phase."""
    cles = [(r.numero_pv, r.jury) for r in resultats]
    en_double_dans_le_fichier = {cle for cle in cles if cles.count(cle) > 1}
    deja_publies = set(
        (
            await db.execute(
                select(Resultat.numero_pv, Resultat.jury).where(
                    Resultat.examen_id == examen.id, Resultat.phase == phase
                )
            )
        ).all()
    )
    conflits = sorted(en_double_dans_le_fichier | (set(cles) & deja_publies))
    if conflits:
        apercu = ", ".join(f"PV {pv} ({jury})" for pv, jury in conflits[:5])
        suite = f" et {len(conflits) - 5} autre(s)" if len(conflits) > 5 else ""
        raise HTTPException(
            status_code=409,
            detail=f"{len(conflits)} candidat(s) ont déjà un résultat pour la phase "
            f"{phase.value} ou figurent deux fois dans la liste : {apercu}{suite}",
        )


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
    request: Request,
    ingestion_id: uuid.UUID,
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
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

    examen = await db.get(Examen, ingestion.examen_id)
    try:
        # Re-checked at publication: the phase may have been closed (or the previous
        # one not yet) since the upload.
        verifier_phase_ouverte(examen, ingestion.phase)
    except ErreurPhase as erreur:
        raise HTTPException(status_code=409, detail=str(erreur)) from erreur

    resultats = construire_resultats(ingestion, examen)
    await _refuser_doublons(resultats, examen, ingestion.phase, db)
    for resultat in resultats:
        db.add(resultat)
    if examen.statut == StatutExamen.PUBLISHED:
        # A new list on an already public exam (typically the next phase of a
        # concours): candidate dashboards follow it and candidates are notified. For an
        # exam not yet public, the same happens when the exam itself is published.
        await db.flush()
        await MatchingService(db).traiter_publication_examen(examen)

    ingestion.statut = StatutIngestion.PUBLIEE
    ingestion.publiee_at = func.now()
    await journaliser_audit(
        db,
        utilisateur_id=current_utilisateur.id,
        administration_id=administration.id,
        action=ActionAuditLog.PUBLISH_INGESTION,
        request=request,
        details={"ingestion_id": str(ingestion.id)},
    )
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
    request: Request,
    ingestion_id: uuid.UUID,
    current_utilisateur: Utilisateur = Depends(get_current_utilisateur),
    administration: Administration = Depends(get_current_administration),
    db: AsyncSession = Depends(get_db),
) -> Ingestion:
    ingestion = await _get_ingestion_ou_404(ingestion_id, administration, db)
    if ingestion.statut != StatutIngestion.PREVISUALISATION:
        raise HTTPException(status_code=409, detail="Cette ingestion n'est pas en attente")

    ingestion.statut = StatutIngestion.REJETEE
    await journaliser_audit(
        db,
        utilisateur_id=current_utilisateur.id,
        administration_id=administration.id,
        action=ActionAuditLog.REJECT_INGESTION,
        request=request,
        details={"ingestion_id": str(ingestion.id)},
    )
    await db.commit()
    await db.refresh(ingestion)
    return ingestion
