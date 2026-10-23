# Terraform Project & DevOps Toolkit

A repository containing modular infrastructure monitoring tools, deployment scripts, and utilities.

## Components

- **[`monitor-app/`](./monitor-app/)**: Modular Linux & AWS EC2 system resource monitor (CPU, memory, disk, network, process tracking, AWS IMDSv2 metadata). Features a hardened Dockerfile and Docker Compose setup in secure mode.
- **[`scripts/install-docker.sh`](./scripts/install-docker.sh)**: Non-interactive unattended installer for Docker Engine and Docker Compose v2 for Ubuntu and Debian.
- **[`scripts/deploy-monitor.sh`](./scripts/deploy-monitor.sh)**: One-command automated deployment script for launching `monitor-app` with Docker Compose.

## Getting Started

### 1. Automated Non-Interactive Deployment (Ubuntu / Debian)
Run the deploy script directly (fetches Compose configuration and pulls `sah1/practice:monitor-app` from Docker Hub in secure mode):

```bash
# If Docker is not installed yet:
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/install-docker.sh | bash

# Deploy monitor-app (fully non-interactive):
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/deploy-monitor.sh | bash
```

### 2. Manual / Local Development
```bash
cd monitor-app
pip install -r requirements.txt
python main.py --once
```

### 3. Build & Push Image to Docker Hub
To publish a new version of `sah1/practice:monitor-app`:

- **Linux / Bash**:
  ```bash
  bash scripts/build-and-push.sh
  ```
- **Windows PowerShell**:
  ```powershell
  .\scripts\build-and-push.ps1
  ```
*(Or push commits to `main` — GitHub Actions automatically builds and pushes the image via `.github/workflows/docker-build-push.yml`)*
