import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.api_key import ApiKey


class StatutPartenaire(str, enum.Enum):
    ACTIF = "ACTIF"
    SUSPENDU = "SUSPENDU"


class Partenaire(TimestampMixin, Base):
    """Un consommateur de l'API B2B (docs/ROADMAP.md § Phase 4) : école privée,
    média, ONG... Transversal aux administrations clientes (pas de
    `administration_id`) — géré par la plateforme (SUPER_ADMIN), au même niveau que
    les `Administration` elles-mêmes."""

    __tablename__ = "partenaires"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    nom: Mapped[str] = mapped_column(String(255))
    contact_nom: Mapped[str] = mapped_column(String(255))
    contact_email: Mapped[str] = mapped_column(String(255))
    statut: Mapped[StatutPartenaire] = mapped_column(
        Enum(StatutPartenaire, name="statut_partenaire"), default=StatutPartenaire.ACTIF
    )

    cles_api: Mapped[list["ApiKey"]] = relationship(back_populates="partenaire")
