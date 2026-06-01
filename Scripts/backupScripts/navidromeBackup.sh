read -s -p "Enter Borg Repository Passphrase: " BORG_PASSPHRASE
echo ""
export BORG_PASSPHRASE

borg create --stats --progress \
    --exclude '~/srv/@music/config/navidrome/navidrome.db*' \
    --exclude '~/srv/@music/config/navidrome/cache' \
    --exclude '~/srv/@music/config/navidrome/artwork' \
    spoob@ciel.local:/run/media/spoob/PersonalBackup/Borg/Navidrome/::{hostname}-{now:%Y-%m-%d_%H:%M} \
    ~/srv/@music
