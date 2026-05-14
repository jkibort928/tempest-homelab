#!/usr/bin/env bash

# Set -e to halt on error
set -e

echo "Pulling latest Fedora Toolbox image..."
podman pull quay.io/fedora/fedora-toolbox:latest

echo "Stopping dev container..."
distrobox stop dev || true

echo "Deleting old dev container"
distrobox rm dev --force

echo "Rebuilding missing containers..."
distrobox assemble create

echo "Container(s) refreshed successfully!"
