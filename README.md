# tempest-homelab

An opinionated, GitOps-driven infrastructure repository for a single-node, bare-metal home server deployment. This repository manages system configuration, containerized microservices, secure overlay networking, and automated backup workflows.

The architecture emphasizes **immutability, security sandboxing (rootless containers), and automated lifecycle management.**

---

## Architecture & Core Technologies

* **Host Operating System:** Fedora IOT (Immutable Linux).
* **Container Orchestration:** Podman managed via **Systemd Quadlets**. Services run rootless, strictly decoupled into custom internal networks (`media-internal`, `immich-internal`) to enforce zero-trust local networking.
* **Network & Security:** Tailscale mesh VPN handles zero-trust secure remote access and ingress routing, bypassing CGNAT constraints without exposing public ports.
* **Performance Tuning:** Custom system tuning via `tuned` profiles (`server-power`) to optimize performance and thermal efficiency on bare-metal hardware.

---

## Repository Highlights

### Automation & Backup Scripts (`/Scripts`)
* **Cron-ready Backups:** Modular Bash scripts (`immichBackup.sh`, `nextcloudBackup.sh`, etc.) that handle database dumps and secure data replication.
* **System Lifecycle Management:** Automates system-level package upgrades, container image updates, and system layering using custom subshell wrappers.

### Declarative Environment Management (`/config`)
* **Custom Package Layouts (`layered.spoob`):** Utilizes a custom, XML-like custom text parsing framework (built in Haskell) to handle bulk-installation tracking and replication of system-layered Linux packages.
* **Isolated Tooling:** Uses Distrobox to sandbox mutable CLI workflows and packages away from the immutable host system.

---
