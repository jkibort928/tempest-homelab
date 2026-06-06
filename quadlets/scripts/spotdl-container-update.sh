podman build --no-cache -t localhost/spotdl-local:latest -f ~/.config/containers/systemd/dockerfiles/spotdl.Dockerfile && systemctl --user restart music-spotdl
