#!/usr/bin/env bash

echo "Triggering SQLite live database dump..."
if "$HOME/quadlets/scripts/music-backup.sh"; then
    echo "Database dump completed."
else
    echo "Error: database dump failed! Aborting."
    exit 1
fi

SERVICE_NAME="Navidrome"
SOURCES=(
    "$HOME/srv/@music"
    "/mnt/disk2/@music"
)
EXCLUDES=(
    '*config/navidrome/navidrome.db*'
    '*config/navidrome/cache'
    '*config/navidrome/artwork'
)

source "$(dirname "$0")/backup-core.sh"
