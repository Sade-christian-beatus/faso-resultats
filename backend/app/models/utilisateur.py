import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.administration import Administration


class RoleUtilisateur(str, enum.Enum):
    # Rôles Faso Résultats (plateforme)
    SUPER_ADMIN = "SUPER_ADMIN"  # équipe Faso Résultats, accès total multi-tenant
    SUPPORT = "SUPPORT"  # support client, lecture seule sur tous les tenants

    # Rôles administration (tenant)
    ADMIN_ADMINISTRATION = "ADMIN_ADMINISTRATION"  # dirigeant de l'administration, tous droits
    OPERATEUR_INGESTION = "OPERATEUR_INGESTION"  # importe et valide les résultats
    OPERATEUR_PUBLICATION = "OPERATEUR_PUBLICATION"  # décide de publier / dépublier
    LECTEUR = "LECTEUR"  # consultation interne uniquement


class Utilisateur(TimestampMixin, Base):
    """Un compte d'accès à l'espace administration. `administration_id` est NULL
    uniquement pour les rôles plateforme (SUPER_ADMIN, SUPPORT) qui ne sont rattachés
    à aucun tenant — voir docs/PIVOT_SAAS_B2G.md § 2.3."""

    __tablename__ = "utilisateurs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    administration_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("administrations.id", ondelete="CASCADE"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    nom_complet: Mapped[str] = mapped_column(String(255))
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[RoleUtilisateur] = mapped_column(Enum(RoleUtilisateur, name="role_utilisateur"))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    derniere_connexion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    administration: Mapped["Administration | None"] = relationship(back_populates="utilisateurs")
