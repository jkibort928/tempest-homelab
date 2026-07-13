#!/usr/bin/env bash

SERVICE_NAME="Vikunja"
SOURCES=("$HOME/srv/@vikunja")
EXCLUDES=()

source "$(dirname "$0")/backup-core.sh"
