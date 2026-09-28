"""resultats : chiffrement au repos de la CNIB, date et lieu de naissance

Revision ID: 5b8e2f41c9d7
Revises: 0694461c8902
Create Date: 2026-09-28 12:00:00.000000

Audit 2026-08-17 : CNIB et date de naissance étaient en clair dans `resultats` alors
qu'elles sont chiffrées dans `profils_candidats`. Chiffre (Fernet, même clé
CANDIDAT_ENCRYPTION_KEY que le profil candidat) :
- resultats.numero_cnib, date_naissance, lieu_naissance ;
- resultats.donnees_brutes et ingestions.apercu_donnees, qui contiennent les mêmes
  données en copie brute (sans eux, le chiffrement des colonnes ne protégerait rien).
Ajoute resultats.numero_cnib_hash (HMAC, même pepper que le profil candidat), indexé,
pour que le rapprochement candidat ↔ résultat par CNIB reste une recherche indexée.

Les données existantes sont chiffrées/déchiffrées ici, par lots : upgrade et downgrade
exigent la même CANDIDAT_ENCRYPTION_KEY et le même CANDIDAT_HASH_PEPPER que
l'application.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from cryptography.fernet import Fernet

from app.config import get_settings
from app.core.security import hash_deterministe

# revision identifiers, used by Alembic.
revision: str = '5b8e2f41c9d7'
down_revision: Union[str, None] = '0694461c8902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TAILLE_LOT = 1000


def _fernet() -> Fernet:
    return Fernet(get_settings().candidat_encryption_key.encode())


def _chiffrer(fernet: Fernet, valeur: str | None) -> str | None:
    return None if valeur is None else fernet.encrypt(valeur.encode()).decode()


def _dechiffrer(fernet: Fernet, valeur: str | None) -> str | None:
    return None if valeur is None else fernet.decrypt(valeur.encode()).decode()


def _par_lots(bind, table: str, colonnes: str):
    """Iterate over a table by primary key batches (never loads the whole table)."""
    dernier_id = None
    while True:
        condition = "" if dernier_id is None else "WHERE id > :dernier_id"
        lignes = bind.execute(
            sa.text(f"SELECT id, {colonnes} FROM {table} {condition} ORDER BY id LIMIT :n"),
            {"dernier_id": dernier_id, "n": _TAILLE_LOT},
        ).all()
        if not lignes:
            return
        yield lignes
        dernier_id = lignes[-1][0]


def upgrade() -> None:
    op.add_column('resultats', sa.Column('numero_cnib_hash', sa.String(length=64), nullable=True))
    op.create_index('ix_resultats_numero_cnib_hash', 'resultats', ['numero_cnib_hash'])

    op.execute("ALTER TABLE resultats ALTER COLUMN numero_cnib TYPE VARCHAR(255)")
    op.execute(
        "ALTER TABLE resultats ALTER COLUMN date_naissance TYPE VARCHAR(255) "
        "USING to_char(date_naissance, 'YYYY-MM-DD')"
    )
    op.execute("ALTER TABLE resultats ALTER COLUMN lieu_naissance TYPE VARCHAR")
    op.execute(
        "ALTER TABLE resultats ALTER COLUMN donnees_brutes TYPE TEXT USING donnees_brutes::text"
    )
    op.execute(
        "ALTER TABLE ingestions ALTER COLUMN apercu_donnees TYPE TEXT USING apercu_donnees::text"
    )

    bind = op.get_bind()
    fernet = _fernet()
    for lot in _par_lots(
        bind, "resultats", "numero_cnib, date_naissance, lieu_naissance, donnees_brutes"
    ):
        for id_, cnib, date_naissance, lieu, brut in lot:
            bind.execute(
                sa.text(
                    "UPDATE resultats SET numero_cnib = :cnib, numero_cnib_hash = :hash, "
                    "date_naissance = :date, lieu_naissance = :lieu, donnees_brutes = :brut "
                    "WHERE id = :id"
                ),
                {
                    "id": id_,
                    "cnib": _chiffrer(fernet, cnib),
                    "hash": hash_deterministe(cnib) if cnib else None,
                    "date": _chiffrer(fernet, date_naissance),
                    "lieu": _chiffrer(fernet, lieu),
                    "brut": _chiffrer(fernet, brut),
                },
            )
    for lot in _par_lots(bind, "ingestions", "apercu_donnees"):
        for id_, apercu in lot:
            bind.execute(
                sa.text("UPDATE ingestions SET apercu_donnees = :apercu WHERE id = :id"),
                {"id": id_, "apercu": _chiffrer(fernet, apercu)},
            )


def downgrade() -> None:
    bind = op.get_bind()
    fernet = _fernet()
    for lot in _par_lots(
        bind, "resultats", "numero_cnib, date_naissance, lieu_naissance, donnees_brutes"
    ):
        for id_, cnib, date_naissance, lieu, brut in lot:
            bind.execute(
                sa.text(
                    "UPDATE resultats SET numero_cnib = :cnib, date_naissance = :date, "
                    "lieu_naissance = :lieu, donnees_brutes = :brut WHERE id = :id"
                ),
                {
                    "id": id_,
                    "cnib": _dechiffrer(fernet, cnib),
                    "date": _dechiffrer(fernet, date_naissance),
                    "lieu": _dechiffrer(fernet, lieu),
                    "brut": _dechiffrer(fernet, brut),
                },
            )
    for lot in _par_lots(bind, "ingestions", "apercu_donnees"):
        for id_, apercu in lot:
            bind.execute(
                sa.text("UPDATE ingestions SET apercu_donnees = :apercu WHERE id = :id"),
                {"id": id_, "apercu": _dechiffrer(fernet, apercu)},
            )

    op.execute(
        "ALTER TABLE ingestions ALTER COLUMN apercu_donnees TYPE JSONB "
        "USING apercu_donnees::jsonb"
    )
    op.execute(
        "ALTER TABLE resultats ALTER COLUMN donnees_brutes TYPE JSONB USING donnees_brutes::jsonb"
    )
    op.execute("ALTER TABLE resultats ALTER COLUMN lieu_naissance TYPE VARCHAR(255)")
    op.execute(
        "ALTER TABLE resultats ALTER COLUMN date_naissance TYPE DATE USING date_naissance::date"
    )
    op.execute("ALTER TABLE resultats ALTER COLUMN numero_cnib TYPE VARCHAR(20)")

    op.drop_index('ix_resultats_numero_cnib_hash', table_name='resultats')
    op.drop_column('resultats', 'numero_cnib_hash')
