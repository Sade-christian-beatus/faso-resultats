"""Peuple la base avec les données minimales pour démarrer en développement.

Idempotent : peut être relancé sans dupliquer l'admin par défaut.
Usage : python seed.py
"""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models import Admin

DEFAULT_ADMIN_EMAIL = "admin@faso-resultats.bf"
DEFAULT_ADMIN_PASSWORD = "ChangeMe123!"


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Admin).where(Admin.email == DEFAULT_ADMIN_EMAIL))
        if result.scalar_one_or_none() is not None:
            print(f"Admin {DEFAULT_ADMIN_EMAIL} existe déjà, rien à faire.")
            return

        admin = Admin(
            email=DEFAULT_ADMIN_EMAIL,
            mot_de_passe_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            nom_complet="Administrateur par défaut",
        )
        db.add(admin)
        await db.commit()
        print(f"Admin par défaut créé : {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}")
        print("Pensez à changer ce mot de passe avant la mise en production.")


if __name__ == "__main__":
    asyncio.run(seed())
