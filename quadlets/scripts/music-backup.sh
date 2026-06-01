#!/bin/bash

# --- CONFIGURATION ---
NAVI_DATA_DIR="$HOME/srv/@music/config/navidrome"
BACKUP_DIR="$HOME/srv/@music/backups"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Get current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="navidrome_db_$TIMESTAMP.bak"

# Execute safe live backup using SQLite inside your data directory
if [ -f "$NAVI_DATA_DIR/navidrome.db" ]; then
    echo "Executing safe live backup inside the container..."
    
    # Trigger SQLite's hot-backup inside the running 'navidrome' container
    if podman exec navidrome sqlite3 /data/navidrome.db ".backup '/backups/$BACKUP_FILENAME'" 2>/dev/null; then
        
        # Verify the file materialized on the host via the mount
        if [ -f "$BACKUP_DIR/$BACKUP_FILENAME" ]; then
        
            gzip "$BACKUP_DIR/$BACKUP_FILENAME"
            echo "Backup successful! Saved to $BACKUP_DIR/$BACKUP_FILENAME.gz"
            
            # Keep only the last 7 days of database backups
            find "$BACKUP_DIR" -name "navidrome_db_*.bak.gz" -mtime +7 -delete
            echo "Old backups cleaned up."
        fi
    else
        echo "CRITICAL ERROR: Failed to execute backup inside the navidrome container."
        echo "Ensure the container is running and 'sqlite3' is available inside the image."
        exit 1
    fi
else
    echo "CRITICAL ERROR: navidrome.db not found in $NAVI_DATA_DIR"
    exit 1
fi
