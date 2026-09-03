"""audit log : nouvelle valeur LOGIN_FAILED sur action_audit_log

Revision ID: 0694461c8902
Revises: 7d03f84b9299
Create Date: 2026-08-17 05:00:00.000000

Audit 2026-08-17 : les échecs de connexion admin n'étaient pas journalisés, rendant
impossible la détection a posteriori d'un brute-force en cours. Accompagne le
verrouillage de compte introduit dans la même session (AdminLoginLockoutService).
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0694461c8902'
down_revision: Union[str, None] = '7d03f84b9299'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE action_audit_log ADD VALUE IF NOT EXISTS 'LOGIN_FAILED'")


def downgrade() -> None:
    # Postgres ne permet pas de retirer une valeur d'un enum sans recréer le type
    # entier ; comme les autres migrations de ce projet ajoutant des valeurs d'enum,
    # le downgrade est un no-op assumé.
    pass
