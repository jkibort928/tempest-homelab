read -s -p "Enter Borg Repository Passphrase: " BORG_PASSPHRASE
echo ""
export BORG_PASSPHRASE

borg create --stats --progress \
    spoob@ciel.local:/run/media/spoob/PersonalBackup/Borg/Nextcloud/::{hostname}-{now:%Y-%m-%d_%H:%M} \
    ~/srv/@nextcloud/data
