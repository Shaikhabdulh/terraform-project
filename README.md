# Terraform Project & DevOps Toolkit

A repository containing modular infrastructure monitoring tools, deployment scripts, and utilities.

## Components

- **[`monitor-app/`](./monitor-app/)**: Modular Linux & AWS EC2 system resource monitor (CPU, memory, disk, network, process tracking, AWS IMDSv2 metadata). Features a hardened Dockerfile and Docker Compose setup in secure mode.
- **[`scripts/install-docker.sh`](./scripts/install-docker.sh)**: Minimal, non-interactive Docker Engine & Compose v2 installer for Ubuntu and Debian.
- **[`scripts/deploy-monitor.sh`](./scripts/deploy-monitor.sh)**: Minimal unattended deployer for `monitor-app`, optimized for EC2 `user_data` or remote one-line execution.
- **[`scripts/build-and-push.sh`](./scripts/build-and-push.sh)**: Minimal build and push script for publishing `sah1/practice:monitor-app` to Docker Hub.

## Getting Started

### 1. EC2 `user_data` / Unattended Deployment (Ubuntu)
Run both steps unattended in an EC2 launch template or bash script:

```bash
#!/bin/bash
# Install Docker
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/install-docker.sh | bash

# Deploy monitor-app non-interactively (optionally pass Read-Only PAT if needed)
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/deploy-monitor.sh | bash -s -- "dckr_pat_..."
```

### 2. Manual / Local Development
```bash
cd monitor-app
pip install -r requirements.txt
python main.py --once
```

### 3. Build & Push Image to Docker Hub
```bash
bash scripts/build-and-push.sh "YOUR_PUSH_TOKEN"
```
