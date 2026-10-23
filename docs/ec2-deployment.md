# EC2 & Cloud-Init Deployment Guide

This guide covers automating the installation and execution of `monitor-app` on AWS EC2 instances (Ubuntu / Debian) using cloud-init and Terraform.

---

## 1. Automated EC2 User Data

When launching an EC2 instance in AWS, paste the following into the **User Data** field:

```bash
#!/bin/bash
set -euo pipefail

# Step 1: Install Docker & Compose v2 non-interactively
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/install-docker.sh | bash

# Step 2: Deploy monitor-app (pulls sah1/practice:monitor-app from Docker Hub)
# Replace <YOUR_READ_ONLY_PAT> with your read-only Docker Hub Personal Access Token
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/deploy-monitor.sh | bash -s -- "<YOUR_READ_ONLY_PAT>"
```

---

## 2. Terraform Integration

In your Terraform configuration, pass the bootstrap script to the `user_data` argument of `aws_instance` or `aws_launch_template`:

```hcl
variable "docker_read_only_pat" {
  type        = string
  description = "Docker Hub Read-Only PAT for pulling images"
  sensitive   = true
}

resource "aws_instance" "monitor_host" {
  ami           = "ami-xxxxxx" # Ubuntu 22.04 LTS or 24.04 LTS
  instance_type = "t3.micro"

  user_data = <<-EOF
              #!/bin/bash
              set -euo pipefail
              curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/install-docker.sh | bash
              curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/deploy-monitor.sh | bash -s -- "${var.docker_read_only_pat}"
              EOF

  tags = {
    Name = "monitor-host"
  }
}
```

---

## 3. Post-Deployment Verification

SSH into your EC2 instance and inspect the running container:

```bash
# Check container status
docker ps

# Follow live resource telemetry in JSON format
cd /opt/monitor-app
docker compose logs -f
```
