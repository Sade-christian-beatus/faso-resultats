"""audit log : journal d'audit des actions admin

Revision ID: f0525fc88905
Revises: a1c9e5f8d3b2
Create Date: 2026-07-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

import app.models.guid

# revision identifiers, used by Alembic.
revision: str = 'f0525fc88905'
down_revision: Union[str, None] = 'a1c9e5f8d3b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

action_audit_log = postgresql.ENUM(
    "LOGIN",
    "CREATE_UTILISATEUR",
    "CREATE_EXAMEN",
    "PUBLISH_EXAMEN",
    "UPLOAD_INGESTION",
    "CORRECT_INGESTION",
    "PUBLISH_INGESTION",
    "REJECT_INGESTION",
    "CREATE_ADMINISTRATION",
    "UPDATE_ADMINISTRATION",
    name="action_audit_log",
)


def upgrade() -> None:
    bind = op.get_bind()
    action_audit_log.create(bind, checkfirst=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", app.models.guid.GUID(), primary_key=True),
        sa.Column(
            "utilisateur_id",
            app.models.guid.GUID(),
            sa.ForeignKey("utilisateurs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "administration_id",
            app.models.guid.GUID(),
            sa.ForeignKey("administrations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "action", postgresql.ENUM(name="action_audit_log", create_type=False), nullable=False
        ),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index("ix_audit_logs_utilisateur_id", "audit_logs", ["utilisateur_id"])
    op.create_index("ix_audit_logs_administration_id", "audit_logs", ["administration_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_administration_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_utilisateur_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    bind = op.get_bind()
    action_audit_log.drop(bind, checkfirst=True)
