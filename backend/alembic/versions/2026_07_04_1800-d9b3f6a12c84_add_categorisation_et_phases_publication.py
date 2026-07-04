"""add categorisation et phases de publication

Revision ID: d9b3f6a12c84
Revises: c7e2a4f91d05
Create Date: 2026-07-04 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd9b3f6a12c84'
down_revision: Union[str, None] = 'c7e2a4f91d05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NOUVEAUX_TYPES_EXAMEN = [
    "BEP", "CAP", "BAC_GENERAL", "BAC_TECHNOLOGIQUE", "BAC_PROFESSIONNEL",
    "CQP", "BQP", "BPT", "CD_CATEGORIE_A", "CD_CATEGORIE_B", "CD_CATEGORIE_C",
    "CD_CATEGORIE_D", "CONCOURS_PROFESSIONNEL", "ARMEE", "POLICE", "DOUANES",
    "GENDARMERIE", "EAUX_FORETS", "SECURITE_PENITENTIAIRE", "AUTRE",
]

categorie_examen = postgresql.ENUM(
    "EXAMEN_SCOLAIRE",
    "CONCOURS_DIRECT",
    "CONCOURS_PROFESSIONNEL",
    "CONCOURS_PARAMILITAIRE",
    name="categorie_examen",
)

source_donnees = postgresql.ENUM(
    "SIGEC_API",
    "FILE_IMPORT",
    "GOUV_PDF_MONITOR",
    "FACEBOOK_SCRAPING",
    "PRESS_MONITORING",
    "MANUAL",
    name="source_donnees",
)

phase_publication = postgresql.ENUM(
    "RESULTAT_UNIQUE",
    "EPREUVES_SPORTIVES",
    "ADMISSIBILITE",
    "ADMISSION_DEFINITIVE",
    "SECOND_TOUR",
    name="phase_publication",
)


def upgrade() -> None:
    bind = op.get_bind()

    # Types Postgres créés une seule fois, puis référencés par les colonnes avec
    # create_type=False (sinon SQLAlchemy tenterait de les recréer pour chaque colonne).
    categorie_examen.create(bind, checkfirst=True)
    source_donnees.create(bind, checkfirst=True)
    phase_publication.create(bind, checkfirst=True)

    for valeur in _NOUVEAUX_TYPES_EXAMEN:
        op.execute(f"ALTER TYPE type_examen ADD VALUE IF NOT EXISTS '{valeur}'")

    op.add_column(
        "examens",
        sa.Column("categorie", postgresql.ENUM(name="categorie_examen", create_type=False), nullable=True),
    )
    op.add_column("examens", sa.Column("serie", sa.String(length=50), nullable=True))
    op.add_column("examens", sa.Column("ministere_tutelle", sa.String(length=255), nullable=True))
    op.add_column(
        "examens",
        sa.Column(
            "source_donnees",
            postgresql.ENUM(name="source_donnees", create_type=False),
            nullable=False,
            server_default="FILE_IMPORT",
        ),
    )
    op.alter_column("examens", "source_donnees", server_default=None)
    op.add_column(
        "examens",
        sa.Column("partenariat_officiel", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("examens", "partenariat_officiel", server_default=None)
    op.add_column(
        "examens",
        sa.Column(
            "phases_publication",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
    )
    op.alter_column("examens", "phases_publication", server_default=None)

    op.add_column(
        "resultats",
        sa.Column(
            "phase",
            postgresql.ENUM(name="phase_publication", create_type=False),
            nullable=False,
            server_default="RESULTAT_UNIQUE",
        ),
    )
    op.alter_column("resultats", "phase", server_default=None)
    op.add_column(
        "resultats", sa.Column("date_publication_phase", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "resultats",
        sa.Column(
            "phase_suivante_attendue",
            postgresql.ENUM(name="phase_publication", create_type=False),
            nullable=True,
        ),
    )

    op.drop_index("ix_resultats_examen_pv_jury", table_name="resultats")
    op.create_index(
        "ix_resultats_examen_pv_jury_phase",
        "resultats",
        ["examen_id", "numero_pv", "jury", "phase"],
    )


def downgrade() -> None:
    op.drop_index("ix_resultats_examen_pv_jury_phase", table_name="resultats")
    op.create_index(
        "ix_resultats_examen_pv_jury", "resultats", ["examen_id", "numero_pv", "jury"]
    )

    op.drop_column("resultats", "phase_suivante_attendue")
    op.drop_column("resultats", "date_publication_phase")
    op.drop_column("resultats", "phase")

    op.drop_column("examens", "phases_publication")
    op.drop_column("examens", "partenariat_officiel")
    op.drop_column("examens", "source_donnees")
    op.drop_column("examens", "ministere_tutelle")
    op.drop_column("examens", "serie")
    op.drop_column("examens", "categorie")

    # Les valeurs ajoutées à l'enum type_examen ne sont pas retirables sans recréer le
    # type (limitation Postgres) — laissées en place au downgrade, inoffensives si
    # inutilisées.

    bind = op.get_bind()
    phase_publication.drop(bind, checkfirst=True)
    source_donnees.drop(bind, checkfirst=True)
    categorie_examen.drop(bind, checkfirst=True)
