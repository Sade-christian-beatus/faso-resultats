import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.guid import GUID

if TYPE_CHECKING:
    from app.models.administration import Administration
    from app.models.ingestion import Ingestion
    from app.models.notification_preinscription import NotificationPreinscription
    from app.models.resultat import Resultat


class CategorieExamen(str, enum.Enum):
    EXAMEN_SCOLAIRE = "EXAMEN_SCOLAIRE"
    CONCOURS_DIRECT = "CONCOURS_DIRECT"
    CONCOURS_PROFESSIONNEL = "CONCOURS_PROFESSIONNEL"
    CONCOURS_PARAMILITAIRE = "CONCOURS_PARAMILITAIRE"


class TypeExamen(str, enum.Enum):
    # Scolaires (DGEC / MENAPLN / MEBAPLN)
    CEP = "CEP"
    BEPC = "BEPC"
    BEP = "BEP"
    CAP = "CAP"
    # BAC conservé tel quel (non-breaking) ; les 3 variantes précisent la série quand connue.
    BAC = "BAC"
    BAC_GENERAL = "BAC_GENERAL"
    BAC_TECHNOLOGIQUE = "BAC_TECHNOLOGIQUE"
    BAC_PROFESSIONNEL = "BAC_PROFESSIONNEL"
    CQP = "CQP"
    BQP = "BQP"
    BPT = "BPT"
    # Concours directs Fonction publique. CONCOURS_DIRECT conservé tel quel (non-breaking) ;
    # les 4 catégories précisent le niveau de diplôme requis quand connu.
    CONCOURS_DIRECT = "CONCOURS_DIRECT"
    CD_CATEGORIE_A = "CD_CATEGORIE_A"
    CD_CATEGORIE_B = "CD_CATEGORIE_B"
    CD_CATEGORIE_C = "CD_CATEGORIE_C"
    CD_CATEGORIE_D = "CD_CATEGORIE_D"
    # Concours professionnels (promotion interne)
    CONCOURS_PROFESSIONNEL = "CONCOURS_PROFESSIONNEL"
    # Concours paramilitaires et spécifiques
    ARMEE = "ARMEE"
    POLICE = "POLICE"
    DOUANES = "DOUANES"
    GENDARMERIE = "GENDARMERIE"
    EAUX_FORETS = "EAUX_FORETS"
    SECURITE_PENITENTIAIRE = "SECURITE_PENITENTIAIRE"
    # Extensible : tout examen/concours ne rentrant pas encore dans une catégorie ci-dessus.
    AUTRE = "AUTRE"


class SourceDonnees(str, enum.Enum):
    """D'où proviennent les résultats d'un examen — voir docs/CONTEXTE_METIER.md § 4.2."""

    SIGEC_API = "SIGEC_API"
    FILE_IMPORT = "FILE_IMPORT"
    GOUV_PDF_MONITOR = "GOUV_PDF_MONITOR"
    FACEBOOK_SCRAPING = "FACEBOOK_SCRAPING"
    PRESS_MONITORING = "PRESS_MONITORING"
    MANUAL = "MANUAL"


class StatutExamen(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Examen(TimestampMixin, Base):
    __tablename__ = "examens"
    __table_args__ = (
        Index("ix_examens_statut_annee", "statut", "annee"),
        Index("ix_examens_administration_statut", "administration_id", "statut"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    # Tenant propriétaire (docs/PIVOT_SAAS_B2G.md § 2.4) — un examen appartient à une
    # seule administration, jamais partagé entre tenants.
    administration_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("administrations.id", ondelete="CASCADE"), nullable=False
    )
    type_examen: Mapped[TypeExamen] = mapped_column(Enum(TypeExamen, name="type_examen"))
    annee: Mapped[int] = mapped_column(Integer)
    libelle: Mapped[str] = mapped_column(String(255))
    statut: Mapped[StatutExamen] = mapped_column(
        Enum(StatutExamen, name="statut_examen"), default=StatutExamen.DRAFT
    )

    # Cartographie du positionnement concurrentiel (docs/CONTEXTE_METIER.md) : tous
    # optionnels ou à valeur par défaut, pour ne rien casser des créations existantes.
    categorie: Mapped[CategorieExamen | None] = mapped_column(
        Enum(CategorieExamen, name="categorie_examen"), nullable=True
    )
    serie: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ministere_tutelle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_donnees: Mapped[SourceDonnees] = mapped_column(
        Enum(SourceDonnees, name="source_donnees"), default=SourceDonnees.FILE_IMPORT
    )
    partenariat_officiel: Mapped[bool] = mapped_column(Boolean, default=False)
    # Phases attendues pour ce type d'examen (ex. concours paramilitaire : sportives,
    # admissibilité, admission définitive) — voir PhasePublication sur Resultat.
    phases_publication: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list
    )
    # Phases closed by an admin, in order (app/services/phases.py): once closed, no new
    # list can be published for it, and a candidate from the previous phase who is not on
    # its lists is told so. Before closure, lists may still be arriving centre by centre.
    phases_cloturees: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list
    )

    administration: Mapped["Administration"] = relationship()
    resultats: Mapped[list["Resultat"]] = relationship(back_populates="examen")
    ingestions: Mapped[list["Ingestion"]] = relationship(back_populates="examen")
    notifications: Mapped[list["NotificationPreinscription"]] = relationship(
        back_populates="examen"
    )
