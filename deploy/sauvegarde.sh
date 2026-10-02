#!/bin/sh
# Daily backup of the production platform (docs/DEPLOIEMENT.md § Sauvegardes).
#
#   deploy/sauvegarde.sh [destination]     (default: /var/backups/faso-resultats)
#
# Saves the database and the official source files (traceability: every published
# result must be traceable to its file). Run it from cron, then copy the destination
# folder OFF the server: a backup kept on the same disk is lost with it.
#
# Not saved here, on purpose: deploy/production.env and its CANDIDAT_ENCRYPTION_KEY.
# Keep that key separately (sealed envelope, password manager): without it the
# encrypted candidate data in these backups cannot be read.
set -eu

cd "$(dirname "$0")/.."
DESTINATION="${1:-/var/backups/faso-resultats}"
HORODATAGE="$(date +%Y%m%d-%H%M)"
CONSERVATION_JOURS=30
COMPOSE="docker compose -f docker-compose.prod.yml --env-file deploy/production.env"

mkdir -p "$DESTINATION"
chmod 700 "$DESTINATION"

$COMPOSE exec -T db pg_dump -U faso -d faso_resultats --format=custom \
    > "$DESTINATION/base-$HORODATAGE.dump"
$COMPOSE run --rm --no-deps -T backend tar czf - -C /app uploads \
    > "$DESTINATION/fichiers-sources-$HORODATAGE.tar.gz"

# An empty file means a failed backup: stop loudly rather than rotate good ones away.
for fichier in "$DESTINATION/base-$HORODATAGE.dump" "$DESTINATION/fichiers-sources-$HORODATAGE.tar.gz"; do
    if [ ! -s "$fichier" ]; then
        echo "ERREUR : sauvegarde vide ($fichier)" >&2
        exit 1
    fi
done

find "$DESTINATION" -name 'base-*.dump' -mtime +$CONSERVATION_JOURS -delete
find "$DESTINATION" -name 'fichiers-sources-*.tar.gz' -mtime +$CONSERVATION_JOURS -delete
echo "Sauvegarde terminée : $DESTINATION (*-$HORODATAGE.*)"
