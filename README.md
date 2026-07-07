# Tempest (Homelab Main Node)

An opinionated, GitOps-driven infrastructure repository for a single-node, bare-metal home server deployment. This repository manages system configuration, containerized microservices, secure overlay networking, and automated backup workflows.

## Hardware Setup
#### Dell Inspiron 3511 (Headless)
* **CPU:** Intel i3-1115G4 (2 Cores / 4 Threads)
* **RAM:** 8GB DDR4
* **Storage:** 2TB Enterprise Samsung 2.5" SATA SSD

## Architecture & Core Technologies

* **Host OS:** Fedora IoT (Immutable/Atomic Linux).
* **Container Orchestration:** Podman managed via **Systemd Quadlets**. Services run rootless and are tightly decoupled into custom internal networks (`media-internal`) to enforce local security isolation.
* **Network & Ingress:** Tailscale mesh VPN handles secure remote access and ingress routing via `tailscale serve`. This safely bypasses carrier network constraints without exposing public firewall ports.
* **Performance Tuning:** Custom system tuning via `tuned` profiles (`server-power`) to optimize power draw and thermals/noise.

## Repository Highlights

### Backup Scripts (`/Scripts`) & Automation
* **Cron-ready Backups:** Modular Bash scripts (`immichBackup.sh`, `nextcloudBackup.sh`, etc.) that handle database dumps and secure data replication via BorgBackup to a local storage target.
* **System Lifecycle Management:** System-level package upgrades, container image updates, and system layering are all handled using custom subshell wrappers for efficent manual administration.

### Declarative Environment Management
* **Custom Package Layouts (`layered.spoob`):** Utilizes a custom, XML-like layout framework (parsed with a custom tool written in Haskell) to track and replicate system-layered packages cleanly.
* **Isolated Tooling:** Uses Distrobox to sandbox mutable CLI environments, keeping development tools entirely separated from the host operating system.


## Sister repository: [Souei](https://github.com/jkibort928/souei-homelab) (Companion Node)
A more powerful compute node that handles heavier tasks (like Immich machine learning).
