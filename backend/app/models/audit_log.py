import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base
from app.models.guid import GUID


class ActionAuditLog(str, enum.Enum):
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    CREATE_UTILISATEUR = "CREATE_UTILISATEUR"
    CREATE_EXAMEN = "CREATE_EXAMEN"
    PUBLISH_EXAMEN = "PUBLISH_EXAMEN"
    UPLOAD_INGESTION = "UPLOAD_INGESTION"
    CORRECT_INGESTION = "CORRECT_INGESTION"
    PUBLISH_INGESTION = "PUBLISH_INGESTION"
    REJECT_INGESTION = "REJECT_INGESTION"
    CREATE_ADMINISTRATION = "CREATE_ADMINISTRATION"
    UPDATE_ADMINISTRATION = "UPDATE_ADMINISTRATION"
    CREATE_PARTENAIRE = "CREATE_PARTENAIRE"
    UPDATE_PARTENAIRE = "UPDATE_PARTENAIRE"
    CREATE_API_KEY = "CREATE_API_KEY"
    REVOKE_API_KEY = "REVOKE_API_KEY"


class AuditLog(Base):
    """Journal d'audit des actions admin (docs/PIVOT_SAAS_B2G.md § 8, item 11) :
    qui a fait quoi, quand, sur quel tenant. Append-only — jamais modifié ni supprimé.

    Les clés étrangères sont en `SET NULL` plutôt qu'en cascade : si un utilisateur ou
    une administration est supprimé, l'entrée d'audit doit survivre (c'est tout
    l'intérêt d'un journal d'audit), seule la référence devient NULL."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    utilisateur_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    administration_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("administrations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[ActionAuditLog] = mapped_column(Enum(ActionAuditLog, name="action_audit_log"))
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    # Métadonnées ciblées (ex. examen_id, ingestion_id) — jamais de données personnelles
    # sensibles (CLAUDE.md), uniquement des identifiants techniques.
    details: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
