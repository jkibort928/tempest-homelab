# Toolbx
alias enter='distrobox enter dev'

# Shortcut
alias db='distrobox'

# Monitoring
alias ctop='podman run --rm -it \
    --security-opt label=disable \
    -v "${XDG_RUNTIME_DIR}/podman/podman.sock:/var/run/docker.sock:Z" \
    quay.io/vektorlab/ctop:latest'
