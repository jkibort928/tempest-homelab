#!/usr/bin/env bash

# Define the base repository path
BASE_REPO="spoob@ciel.local:/run/media/spoob/bongusbackup/ServerBorgs"

# Prompt for passphrase if not already exported in the current session
if [ -z "$BORG_PASSPHRASE" ]; then
    read -s -p "Enter Borg Repository Passphrase: " BORG_PASSPHRASE
    echo ""
    export BORG_PASSPHRASE
fi

# Build exclude arguments dynamically from the EXCLUDES array
BORG_EXCLUDE_ARGS=()
for excl in "${EXCLUDES[@]}"; do
    BORG_EXCLUDE_ARGS+=("--exclude" "$excl")
done

# Execute the backup
borg create --stats --progress \
    "${BORG_EXCLUDE_ARGS[@]}" \
    "${BASE_REPO}/${SERVICE_NAME}/::{hostname}-{now:%Y-%m-%d_%H:%M}" \
    "${SOURCES[@]}"
