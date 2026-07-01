read -s -p "Enter Borg Repository Passphrase: " BORG_PASSPHRASE
echo ""
export BORG_PASSPHRASE

echo "Triggering SQLite live database dump..."
if "$HOME/quadlets/scripts/music-backup.sh"; then
    echo "Database dump completed."
else
    echo "Error: database dump failed! Aborting."
    exit 1
fi

borg create --stats --progress \
    --exclude '~/srv/@music/config/navidrome/navidrome.db*' \
    --exclude '~/srv/@music/config/navidrome/cache' \
    --exclude '~/srv/@music/config/navidrome/artwork' \
    spoob@ciel.local:/run/media/spoob/PersonalBackup/Borg/Navidrome/::{hostname}-{now:%Y-%m-%d_%H:%M} \
    ~/srv/@music
