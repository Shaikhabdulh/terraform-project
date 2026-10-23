# Terraform Project & DevOps Toolkit

A repository containing modular infrastructure monitoring tools, deployment scripts, and utilities.

## Components

- **[`monitor-app/`](./monitor-app/)**: Modular Linux & AWS EC2 system resource monitor (CPU, memory, disk, network, process tracking, AWS IMDSv2 metadata). Features a hardened Dockerfile and Docker Compose setup in secure mode.
- **[`scripts/install-docker.sh`](./scripts/install-docker.sh)**: Non-interactive unattended installer for Docker Engine and Docker Compose v2 for Ubuntu and Debian.
- **[`scripts/deploy-monitor.sh`](./scripts/deploy-monitor.sh)**: One-command automated deployment script for launching `monitor-app` with Docker Compose.

## Getting Started

### 1. System Monitor
```bash
cd monitor-app
pip install -r requirements.txt
python main.py --once
```

### 2. Docker & Compose v2 Installer
```bash
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/install-docker.sh | bash
```
