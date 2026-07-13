#!/usr/bin/env bash

echo "Triggering SQLite live database dump..."
if "$HOME/quadlets/scripts/music-backup.sh"; then
    echo "Database dump completed."
else
    echo "Error: database dump failed! Aborting."
    exit 1
fi

SERVICE_NAME="Navidrome"
SOURCES=("$HOME/srv/@music")
EXCLUDES=(
    '~/srv/@music/config/navidrome/navidrome.db*'
    '~/srv/@music/config/navidrome/cache'
    '~/srv/@music/config/navidrome/artwork'
)

source "$(dirname "$0")/backup-core.sh"
