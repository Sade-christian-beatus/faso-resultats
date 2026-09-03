import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.partenaire import Partenaire


class StatutApiKey(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOQUEE = "REVOQUEE"


class ApiKey(TimestampMixin, Base):
    """Clé d'accès à l'API B2B (docs/ROADMAP.md § Phase 4). La clé en clair n'est
    jamais stockée : seul son hash HMAC (`security.hash_cle_api`, pepper dédié —
    jamais celui des données candidat) est conservé, avec un préfixe non sensible
    pour que le partenaire identifie sa clé sans revoir le secret complet.

    `tier`/`quota_quotidien` : pas de facturation automatisée pour l'instant (grille
    tarifaire non tranchée, voir docs/ROADMAP.md § Phase 4) — juste un quota
    configurable manuellement par le SUPER_ADMIN à la création de la clé."""

    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_cle_hash", "cle_hash", unique=True),
        Index("ix_api_keys_partenaire_id", "partenaire_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    partenaire_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("partenaires.id", ondelete="CASCADE")
    )
    prefixe: Mapped[str] = mapped_column(String(20))
    cle_hash: Mapped[str] = mapped_column(String(64))
    tier: Mapped[str] = mapped_column(String(50), default="STANDARD")
    quota_quotidien: Mapped[int] = mapped_column(Integer, default=1000)
    statut: Mapped[StatutApiKey] = mapped_column(
        Enum(StatutApiKey, name="statut_api_key"), default=StatutApiKey.ACTIVE
    )
    derniere_utilisation: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    partenaire: Mapped["Partenaire"] = relationship(back_populates="cles_api")
