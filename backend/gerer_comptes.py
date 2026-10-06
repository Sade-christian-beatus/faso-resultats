"""Gestion des comptes admin en ligne de commande (docs/GUIDE_LOCAL.md § 5).

Aucun endpoint de l'API ne permet de changer un mot de passe ni de créer un
SUPER_ADMIN : ce script couvre ces opérations, à lancer sur la machine qui a
accès à la base (comme `seed.py`). Le mot de passe est demandé au clavier, jamais
passé en argument (il resterait dans l'historique du shell).

Usage :
    python gerer_comptes.py lister
    python gerer_comptes.py mot-de-passe EMAIL
    python gerer_comptes.py creer-super-admin EMAIL --nom "Prénom NOM"
    python gerer_comptes.py desactiver EMAIL
    python gerer_comptes.py activer EMAIL
    python gerer_comptes.py debloquer EMAIL

Non journalisé dans `AuditLog` : réservé à l'exploitant de la plateforme, pas
exposé aux administrations clientes.
"""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import cache_delete
from app.core.security import hash_password
from app.models import RoleUtilisateur, Utilisateur
from app.services.admin.login_lockout_service import (
    _cle_tentatives,
    _cle_verrouillage,
)

LONGUEUR_MIN_MOT_DE_PASSE = 8  # même règle que UtilisateurInitialCreate


class ErreurCompte(Exception):
    """Erreur métier affichée telle quelle à l'utilisateur du script."""


def valider_mot_de_passe(mot_de_passe: str) -> None:
    if len(mot_de_passe) < LONGUEUR_MIN_MOT_DE_PASSE:
        raise ErreurCompte(
            f"Mot de passe trop court ({LONGUEUR_MIN_MOT_DE_PASSE} caractères minimum)."
        )


async def _get_utilisateur(db: AsyncSession, email: str) -> Utilisateur:
    result = await db.execute(select(Utilisateur).where(Utilisateur.email == email))
    utilisateur = result.scalar_one_or_none()
    if utilisateur is None:
        raise ErreurCompte(f"Aucun compte avec l'email {email}.")
    return utilisateur


async def debloquer(email: str) -> None:
    """Lève le verrouillage après échecs de connexion (AdminLoginLockoutService)."""
    await cache_delete(_cle_tentatives(email))
    await cache_delete(_cle_verrouillage(email))


async def lister(db: AsyncSession) -> list[Utilisateur]:
    result = await db.execute(
        select(Utilisateur)
        .options(selectinload(Utilisateur.administration))
        .order_by(Utilisateur.email)
    )
    return list(result.scalars().all())


async def changer_mot_de_passe(db: AsyncSession, email: str, mot_de_passe: str) -> None:
    valider_mot_de_passe(mot_de_passe)
    utilisateur = await _get_utilisateur(db, email)
    utilisateur.mot_de_passe_hash = hash_password(mot_de_passe)
    await db.commit()
    await debloquer(email)


async def creer_super_admin(
    db: AsyncSession, email: str, nom_complet: str, mot_de_passe: str
) -> Utilisateur:
    valider_mot_de_passe(mot_de_passe)
    existant = await db.execute(select(Utilisateur).where(Utilisateur.email == email))
    if existant.scalar_one_or_none() is not None:
        raise ErreurCompte(f"Un compte avec l'email {email} existe déjà.")
    utilisateur = Utilisateur(
        administration_id=None,
        email=email,
        mot_de_passe_hash=hash_password(mot_de_passe),
        nom_complet=nom_complet,
        role=RoleUtilisateur.SUPER_ADMIN,
    )
    db.add(utilisateur)
    await db.commit()
    return utilisateur


async def changer_statut(db: AsyncSession, email: str, actif: bool) -> None:
    utilisateur = await _get_utilisateur(db, email)
    utilisateur.actif = actif
    await db.commit()


def _demander_mot_de_passe() -> str:
    mot_de_passe = getpass.getpass("Nouveau mot de passe : ")
    if getpass.getpass("Confirmer le mot de passe : ") != mot_de_passe:
        raise ErreurCompte("Les deux saisies ne correspondent pas.")
    valider_mot_de_passe(mot_de_passe)
    return mot_de_passe


async def _executer(args: argparse.Namespace) -> None:
    # Import tardif : `app.database` lit la configuration (.env) à l'import, inutile
    # pour --help et gênant pour les tests qui fournissent leur propre session.
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        if args.commande == "lister":
            for u in await lister(db):
                tenant = u.administration.code if u.administration else "(plateforme)"
                etat = "actif" if u.actif else "DÉSACTIVÉ"
                print(f"{u.email:40} {u.role.value:24} {tenant:15} {etat}")
        elif args.commande == "mot-de-passe":
            await _get_utilisateur(db, args.email)  # échoue avant de demander la saisie
            await changer_mot_de_passe(db, args.email, _demander_mot_de_passe())
            print(f"Mot de passe de {args.email} modifié.")
        elif args.commande == "creer-super-admin":
            await creer_super_admin(db, args.email, args.nom, _demander_mot_de_passe())
            print(f"SUPER_ADMIN {args.email} créé.")
        elif args.commande in ("desactiver", "activer"):
            await changer_statut(db, args.email, actif=args.commande == "activer")
            print(f"Compte {args.email} {'activé' if args.commande == 'activer' else 'désactivé'}.")
        elif args.commande == "debloquer":
            await debloquer(args.email)
            print(f"Verrouillage de connexion levé pour {args.email}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gestion des comptes admin Faso Résultats.")
    sous = parser.add_subparsers(dest="commande", required=True)
    sous.add_parser("lister", help="Lister les comptes admin")
    for nom, aide in [
        ("mot-de-passe", "Changer le mot de passe d'un compte"),
        ("desactiver", "Désactiver un compte (connexion refusée)"),
        ("activer", "Réactiver un compte"),
        ("debloquer", "Lever le verrouillage après échecs de connexion"),
    ]:
        sous.add_parser(nom, help=aide).add_argument("email")
    creation = sous.add_parser("creer-super-admin", help="Créer un compte SUPER_ADMIN")
    creation.add_argument("email")
    creation.add_argument("--nom", required=True, help="Nom complet")

    try:
        asyncio.run(_executer(parser.parse_args()))
    except ErreurCompte as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
