wake() {
    if [ -z "$1" ]; then
        echo "Usage: wake MAC_ADDRESS (e.g., wake 00:11:22:33:44:55)"
        return 1
    fi

    # Clean the MAC address (remove colons or dashes)
    local mac=$(echo "$1" | tr -d ':-')

    # Construct the magic packet (6 bytes of FF followed by the MAC address 16 times)
    local packet=$(printf 'f%.0s' {1..12}; printf "$mac%.0s" {1..16})

    # Convert hex string to binary data and broadcast it to the local network over UDP port 9
    echo -n "$packet" | xxd -r -p > /dev/udp/255.255.255.255/9 2>/dev/null

    echo "Magic packet sent to $1"
}
export -f wake

# Layer 2 Wake-on-LAN via Ephemeral Podman Container
etherwake() {
    if [ -z "$1" ]; then
        echo "Usage: etherwake MAC_ADDRESS (e.g., etherwake 00:11:22:33:44:55)"
        return 1
    fi
    
    # Capitalize the MAC address to avoid parsing issues with some utilities
    local mac=$(echo "$1" | tr '[:lower:]' '[:upper:]')
    
    echo "Sending Layer 2 Magic Packet via Podman..."
    sudo podman run --rm --net=host -e MAC="$mac" r0gger/docker-wake-on-lan
}
export -f etherwake