import uuid

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActionAuditLog, AuditLog


async def journaliser_audit(
    db: AsyncSession,
    *,
    utilisateur_id: uuid.UUID | None,
    administration_id: uuid.UUID | None,
    action: ActionAuditLog,
    request: Request,
    details: dict | None = None,
) -> None:
    """Trace une action admin (docs/PIVOT_SAAS_B2G.md § 8, item 11). Append-only : ne
    jamais loguer de données personnelles sensibles (CLAUDE.md), uniquement des
    identifiants techniques dans `details`."""
    db.add(
        AuditLog(
            utilisateur_id=utilisateur_id,
            administration_id=administration_id,
            action=action,
            ip=request.client.host if request.client else None,
            details=details,
        )
    )
