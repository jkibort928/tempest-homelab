#!/usr/bin/env bash

# Prompt for the passphrase once
if [ -z "$BORG_PASSPHRASE" ]; then
    read -s -p "Enter Borg Repository Passphrase: " BORG_PASSPHRASE
    echo ""
    export BORG_PASSPHRASE
fi

# Define the scripts to execute explicitly to avoid running unintended files
SCRIPTS=(
    "immichBackup.sh"
    "nextcloudBackup.sh"
    "vikunjaBackup.sh"
)

SCRIPT_DIR="$(dirname "$0")"

for script in "${SCRIPTS[@]}"; do
    echo "========================================"
    echo "Starting backup: $script"
    echo "========================================"
    
    if "$SCRIPT_DIR/$script"; then
        echo "[OK] Completed: $script"
    else
        echo "[ERROR] Failed: $script"
    fi
    echo ""
done

echo "All backup tasks finished."
