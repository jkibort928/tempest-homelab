#!/usr/bin/env bash

CONFIG_FILE="$HOME/.config/tailscale/myServices.conf"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

echo "Wiping current Tailscale serve paths..."
sudo tailscale serve reset

echo "Registering services from config..."
while IFS=":" read -r svc port || [[ -n "$svc" ]]; do
    # Safely skip empty lines and comments
    [[ -z "$svc" || "$svc" =~ ^# ]] && continue
    
    # Strip accidental whitespace
    svc=$(echo "$svc" | tr -d '[:space:]')
    port=$(echo "$port" | tr -d '[:space:]')

    echo "  -> Routing svc:$svc to local port $port..."
    sudo tailscale serve --bg --service="svc:$svc" "$port"
done < "$CONFIG_FILE"

echo "Tailscale serve configuration successfully updated!"
