# Ensure spoober is installed before running
if ! command -v spoober &> /dev/null; then
    echo "Error: 'spoober' command not found or not in PATH." >&2
    exit 1
fi

# Spoobing it
COMPILED_PACKAGES=$(spoober --all ~/.config/distrobox/boxPackages.spoob)

echo "Generating transient distrobox.ini configuration..."
cat << EOF > /tmp/transient-distrobox.ini
[dev]
image=quay.io/fedora/fedora-toolbox:latest
root=false
start_now=true
additional_packages="${COMPILED_PACKAGES}"
EOF

echo "Wiping stale 'dev' container namespace..."
distrobox stop dev || true
distrobox rm dev --force

echo "Assembling fresh dev sandbox using compiled modules..."
distrobox assemble create --file /tmp/transient-distrobox.ini

echo "Clearing temporary deployment manifests..."
rm -f /tmp/transient-distrobox.ini

echo "Done."
