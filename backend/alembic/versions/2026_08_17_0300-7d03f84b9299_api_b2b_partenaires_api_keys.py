"""API B2B : partenaires, api_keys (docs/ROADMAP.md § Phase 4)

Revision ID: 7d03f84b9299
Revises: 8f2cc3339226
Create Date: 2026-08-17 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

import app.models.guid

# revision identifiers, used by Alembic.
revision: str = '7d03f84b9299'
down_revision: Union[str, None] = '8f2cc3339226'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

statut_partenaire = postgresql.ENUM("ACTIF", "SUSPENDU", name="statut_partenaire")
statut_api_key = postgresql.ENUM("ACTIVE", "REVOQUEE", name="statut_api_key")

_NOUVELLES_ACTIONS_AUDIT = [
    "CREATE_PARTENAIRE",
    "UPDATE_PARTENAIRE",
    "CREATE_API_KEY",
    "REVOKE_API_KEY",
]


def upgrade() -> None:
    bind = op.get_bind()
    statut_partenaire.create(bind, checkfirst=True)
    statut_api_key.create(bind, checkfirst=True)

    for valeur in _NOUVELLES_ACTIONS_AUDIT:
        op.execute(f"ALTER TYPE action_audit_log ADD VALUE IF NOT EXISTS '{valeur}'")

    op.create_table(
        "partenaires",
        sa.Column("id", app.models.guid.GUID(), primary_key=True),
        sa.Column("nom", sa.String(length=255), nullable=False),
        sa.Column("contact_nom", sa.String(length=255), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column(
            "statut",
            postgresql.ENUM(name="statut_partenaire", create_type=False),
            nullable=False,
            server_default="ACTIF",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.alter_column("partenaires", "statut", server_default=None)

    op.create_table(
        "api_keys",
        sa.Column("id", app.models.guid.GUID(), primary_key=True),
        sa.Column(
            "partenaire_id",
            app.models.guid.GUID(),
            sa.ForeignKey("partenaires.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prefixe", sa.String(length=20), nullable=False),
        sa.Column("cle_hash", sa.String(length=64), nullable=False),
        sa.Column("tier", sa.String(length=50), nullable=False, server_default="STANDARD"),
        sa.Column("quota_quotidien", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column(
            "statut",
            postgresql.ENUM(name="statut_api_key", create_type=False),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("derniere_utilisation", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.alter_column("api_keys", "tier", server_default=None)
    op.alter_column("api_keys", "quota_quotidien", server_default=None)
    op.alter_column("api_keys", "statut", server_default=None)
    op.create_index("ix_api_keys_cle_hash", "api_keys", ["cle_hash"], unique=True)
    op.create_index("ix_api_keys_partenaire_id", "api_keys", ["partenaire_id"])


def downgrade() -> None:
    op.drop_index("ix_api_keys_partenaire_id", table_name="api_keys")
    op.drop_index("ix_api_keys_cle_hash", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_table("partenaires")

    bind = op.get_bind()
    statut_api_key.drop(bind, checkfirst=True)
    statut_partenaire.drop(bind, checkfirst=True)

    # Les valeurs ajoutées à action_audit_log ne sont pas retirables sans recréer le
    # type (limitation Postgres, même choix que les migrations précédentes de ce
    # projet) — laissées en place au downgrade, inoffensives si inutilisées.
