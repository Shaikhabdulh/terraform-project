# Documentation Index & Architecture Map

Welcome to the documentation for **Terraform Project & DevOps Toolkit**. This project provides modular system monitoring, hardened Docker containerization, and unattended Linux automation scripts for cloud infrastructure (AWS EC2).

---

## Architecture Overview

```
                      +---------------------------------------+
                      |       GitHub Repository / CI/CD       |
                      |  - Codebase & Unit Tests              |
                      |  - GitHub Actions (Docker Publish)    |
                      +-------------------+-------------------+
                                          |
                                          v
                              Docker Hub Image Registry
                            sah1/practice:monitor-app
                                          |
                        +-----------------+-----------------+
                        |                                   |
                        v                                   v
             [Target Host: AWS EC2]              [Developer Workstation]
        - install-docker.sh (one-liner)         - monitor-app local dev
        - deploy-monitor.sh (secure pull)       - build-and-push.sh
        - Read-Only PAT Authentication          - Read/Write Push Token
```

---

## Documentation Map

| Document | Purpose |
| :--- | :--- |
| **[AWS Secrets Manager & RDS MySQL](./aws-secrets-manager-rds.md)** | Production architecture for private subnet RDS MySQL, IAM instance role authentication, and autoscaling alerts. |
| **[EC2 & User Data Deployment](./ec2-deployment.md)** | Step-by-step guide to provisioning via EC2 `user_data`, Terraform, or Cloud-Init. |
| **[Security & Hardening Profile](./security.md)** | Security configurations, container isolation, and safe token management. |
| **[`monitor-app/README.md`](../monitor-app/README.md)** | Detailed documentation for the Python monitoring engine, metrics, and thresholds. |
| **[`scripts/`](../scripts/)** | Minimal, unattended Linux bash scripts for Docker installation, building, and deployment. |

---

## Quick Reference

### 1. Unattended EC2 Bootstrap (User Data)
```bash
#!/bin/bash
set -e

# 1. Install Docker & Compose v2 plugin
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/install-docker.sh | bash

# 2. Deploy monitor-app container (passes Read-Only PAT & optional Secrets Manager name)
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/deploy-monitor.sh | bash -s -- "<YOUR_READ_ONLY_PAT>" "prod/sysmon/rds-mysql"
```

### 2. Secret Management
> [!IMPORTANT]
> Actual personal access tokens (PAT) must **never** be committed to Git. Store them in local ignored environment files (such as `.docker-tokens.env`) and inject them at runtime via CI/CD secrets or instance user data.
