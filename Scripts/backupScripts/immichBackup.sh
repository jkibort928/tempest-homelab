#!/usr/bin/env bash

SERVICE_NAME="Immich"

SOURCES=(
    "$HOME/srv/@immich/photos"
    "/mnt/disk2/@immich"
)
EXCLUDES=(
    '*thumbs'
    '*encoded-video'
)

source "$(dirname "$0")/backup-core.sh"
