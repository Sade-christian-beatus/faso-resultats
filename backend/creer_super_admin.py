"""Create the first SUPER_ADMIN account of a production platform.

seed.py must never run in production: it creates fictitious administrations,
exams and results, and accounts with a public default password. This script
creates a single super-admin and nothing else.

Usage (production stack, see docs/DEPLOIEMENT.md):
    docker compose -f docker-compose.prod.yml --env-file deploy/production.env \\
        run --rm backend python creer_super_admin.py

The password is typed interactively (never on the command line, which would
leave it in the shell history) and stored as a bcrypt hash only.
"""

import asyncio
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models import RoleUtilisateur, Utilisateur

LONGUEUR_MIN_MOT_DE_PASSE = 12


class ErreurCreation(ValueError):
    """Shown as-is to the operator (French)."""


async def creer_super_admin(
    session: AsyncSession, email: str, nom_complet: str, mot_de_passe: str
) -> Utilisateur:
    email = email.strip().lower()
    if "@" not in email:
        raise ErreurCreation("Adresse e-mail invalide.")
    if not nom_complet.strip():
        raise ErreurCreation("Le nom complet est obligatoire.")
    if len(mot_de_passe) < LONGUEUR_MIN_MOT_DE_PASSE:
        raise ErreurCreation(
            f"Le mot de passe doit faire au moins {LONGUEUR_MIN_MOT_DE_PASSE} caractères."
        )
    existant = await session.scalar(select(Utilisateur).where(Utilisateur.email == email))
    if existant is not None:
        raise ErreurCreation(f"Un compte existe déjà pour {email}.")

    utilisateur = Utilisateur(
        email=email,
        mot_de_passe_hash=hash_password(mot_de_passe),
        nom_complet=nom_complet.strip(),
        role=RoleUtilisateur.SUPER_ADMIN,
        administration_id=None,
        actif=True,
    )
    session.add(utilisateur)
    await session.commit()
    return utilisateur


async def main() -> int:
    email = input("E-mail du super-admin : ")
    nom_complet = input("Nom complet : ")
    mot_de_passe = getpass.getpass("Mot de passe (12 caractères minimum) : ")
    if getpass.getpass("Confirmez le mot de passe : ") != mot_de_passe:
        print("Les deux mots de passe ne correspondent pas.", file=sys.stderr)
        return 1
    async with AsyncSessionLocal() as session:
        try:
            utilisateur = await creer_super_admin(session, email, nom_complet, mot_de_passe)
        except ErreurCreation as erreur:
            print(erreur, file=sys.stderr)
            return 1
    print(f"Super-admin créé : {utilisateur.email}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
