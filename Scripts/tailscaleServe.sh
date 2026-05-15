#!/usr/bin/env bash
sudo tailscale serve reset
sudo tailscale serve --bg --service=svc:photos 2283
sudo tailscale serve --bg --service=svc:tasks 3456
sudo tailscale serve --bg --service=svc:media 8096
sudo tailscale serve --bg --service=svc:anime 43211
