"""Purge quotidienne des données candidat (docs/PROFIL_CANDIDAT_UNIFIE.md § 7,
docs/APDP_PROFIL_CANDIDAT.md § 5) : candidatures orphelines expirées (administration
résiliée depuis plus de 6 mois) et profils candidats inactifs.

Pas de file de tâches en Phase 1 (RQ prévu en Phase 2, voir CLAUDE.md) : ce script
est prévu pour être planifié via cron côté infrastructure, pas exécuté depuis
l'application elle-même.

Usage : python purge_candidats.py
"""

import asyncio

from app.database import AsyncSessionLocal
from app.services.candidat.purge_service import (
    purger_candidatures_administration_resiliee_expirees,
    purger_profils_inactifs,
)


async def purger() -> None:
    async with AsyncSessionLocal() as db:
        nb_candidatures = await purger_candidatures_administration_resiliee_expirees(db)
        nb_profils = await purger_profils_inactifs(db)
        await db.commit()
        print(f"{nb_candidatures} candidature(s) orpheline(s) expirée(s) supprimée(s).")
        print(f"{nb_profils} profil(s) candidat inactif(s) supprimé(s).")


if __name__ == "__main__":
    asyncio.run(purger())
