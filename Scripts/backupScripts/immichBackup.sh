read -s -p "Enter Borg Repository Passphrase: " BORG_PASSPHRASE
echo ""
export BORG_PASSPHRASE

borg create --stats --progress \
    --exclude '~/srv/@immich/photos/thumbs' \
    --exclude '~/srv/@immich/photos/encoded-video' \
    spoob@ciel.local:/run/media/spoob/PersonalBackup/Borg/Immich/::{hostname}-{now:%Y-%m-%d_%H:%M} \
    ~/srv/@immich/photos
