import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.guid import GUID


class ActionJournalConsultation(str, enum.Enum):
    INSCRIPTION = "INSCRIPTION"
    LOGIN = "LOGIN"
    VIEW_DASHBOARD = "VIEW_DASHBOARD"
    ADD_CANDIDATURE = "ADD_CANDIDATURE"
    DELETE_CANDIDATURE = "DELETE_CANDIDATURE"
    UPDATE_PREFERENCES = "UPDATE_PREFERENCES"
    DELETE_ACCOUNT = "DELETE_ACCOUNT"
    EXPORT_DONNEES = "EXPORT_DONNEES"


class JournalConsultationProfil(Base):
    """Journal d'audit du profil candidat, immuable (append-only) — conformité APDP
    (docs/PROFIL_CANDIDAT_UNIFIE.md § 3, § 7). Jamais modifié ni supprimé, sauf lors de
    la purge complète d'un profil (droit à l'oubli)."""

    __tablename__ = "journal_consultations_profil"
    __table_args__ = {"schema": "plateforme"}

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    profil_candidat_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("plateforme.profils_candidats.id", ondelete="CASCADE"),
        index=True,
    )
    action: Mapped[ActionJournalConsultation] = mapped_column(
        Enum(ActionJournalConsultation, name="action_journal_consultation")
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
