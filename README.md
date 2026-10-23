# Terraform Project & DevOps Toolkit

A repository containing modular infrastructure monitoring tools, deployment scripts, and utilities.

## Components

- **[`monitor-app/`](./monitor-app/)**: Modular Linux & AWS EC2 system resource monitor (CPU, memory, disk, network, process tracking, AWS IMDSv2 metadata). Features a hardened Dockerfile and Docker Compose setup in secure mode.
- **[`scripts/install-docker.sh`](./scripts/install-docker.sh)**: Minimal, non-interactive Docker Engine & Compose v2 installer for Ubuntu and Debian.
- **[`scripts/deploy-monitor.sh`](./scripts/deploy-monitor.sh)**: Minimal unattended deployer for `monitor-app`, optimized for EC2 `user_data` or remote one-line execution.
- **[`scripts/build-and-push.sh`](./scripts/build-and-push.sh)**: Minimal build and push script for publishing `sah1/practice:monitor-app` to Docker Hub.
- **[`docs/index.md`](./docs/index.md)**: Architecture map, deployment guides, and security documentation.

## Getting Started

### 1. EC2 `user_data` / Unattended Deployment (Ubuntu)
You can paste this bootstrap block directly into an EC2 launch template or user data script:

```bash
#!/bin/bash
set -e

# 1. Install Docker & Compose v2 unattended
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/install-docker.sh | bash

# 2. Deploy monitor-app (passes Read-Only PAT non-interactively)
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/deploy-monitor.sh | bash -s -- "<YOUR_READ_ONLY_PAT>"
```

> [!TIP]
> Retrieve your actual Read-Only PAT from your local [`.docker-tokens.env`](./.docker-tokens.env) file (which is git-ignored to prevent exposing tokens to public repositories).

### 2. Manual / Local Development
```bash
cd monitor-app
pip install -r requirements.txt
python main.py --once
```

### 3. Build & Push Image to Docker Hub
```bash
bash scripts/build-and-push.sh "<YOUR_PUSH_TOKEN>"
```

---

## Documentation

For full guides and architecture specifications, visit the **[Documentation Index](./docs/index.md)**:
- [EC2 & Cloud-Init Deployment](./docs/ec2-deployment.md)
- [Security & Hardening Profile](./docs/security.md)
