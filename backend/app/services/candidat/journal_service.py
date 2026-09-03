import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal_consultation_profil import (
    ActionJournalConsultation,
    JournalConsultationProfil,
)


async def journaliser(
    db: AsyncSession,
    profil_candidat_id: uuid.UUID,
    action: ActionJournalConsultation,
    request: Request,
) -> None:
    """Trace chaque accès au profil candidat (append-only, conformité CIL —
    docs/PROFIL_CANDIDAT_UNIFIE.md § 3, § 7)."""
    db.add(
        JournalConsultationProfil(
            profil_candidat_id=profil_candidat_id,
            action=action,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    )
