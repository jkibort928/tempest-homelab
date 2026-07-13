#!/usr/bin/env bash

SERVICE_NAME="Immich"
SOURCES=("$HOME/srv/@immich/photos")
EXCLUDES=(
    '~/srv/@immich/photos/thumbs'
    '~/srv/@immich/photos/encoded-video'
)

source "$(dirname "$0")/backup-core.sh"
