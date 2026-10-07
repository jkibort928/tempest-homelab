#!/usr/bin/env bash

# Main Drive
MAIN_LUKS_UUID="5fc2216f-ff1c-4845-b0b9-5a600d214a70"
sudo systemd-cryptenroll --wipe-slot=tpm2 /dev/disk/by-uuid/$MAIN_LUKS_UUID
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/disk/by-uuid/$MAIN_LUKS_UUID

# External Drive 1
EXT1_LUKS_UUID="cbfbc6d5-891b-4156-9394-6c0880b5ecb2"
sudo systemd-cryptenroll --wipe-slot=tpm2 /dev/disk/by-uuid/$EXT1_LUKS_UUID
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 /dev/disk/by-uuid/$EXT1_LUKS_UUID

sudo rpm-ostree initramfs-etc --force-sync
