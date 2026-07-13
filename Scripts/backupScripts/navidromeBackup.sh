SERVICE_NAME="Navidrome"
SOURCES=("$HOME/srv/@music")
EXCLUDES=(
    '~/srv/@music/config/navidrome/navidrome.db*'
    '~/srv/@music/config/navidrome/cache'
    '~/srv/@music/config/navidrome/artwork'
)

source "$(dirname "$0")/backup_core.sh"
