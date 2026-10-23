#!/usr/bin/env bash
#
# Minimal unattended deployer for monitor-app (EC2 user_data compatible)
#
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

DOCKER_USER="${DOCKER_USER:-sah1}"
DOCKER_PAT="${1:-${DOCKER_PAT:-}}"
RAW_COMPOSE_URL="https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/monitor-app/docker-compose.yml"
APP_DIR="/opt/monitor-app"

# Authenticate if PAT provided
if [ -n "$DOCKER_PAT" ]; then
    echo "$DOCKER_PAT" | docker login -u "$DOCKER_USER" --password-stdin >/dev/null 2>&1 || true
fi

# Setup directory and compose file
mkdir -p "$APP_DIR"
if [ ! -f "${APP_DIR}/docker-compose.yml" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$PWD}")" 2>/dev/null && pwd || echo "$PWD")"
    if [ -f "${SCRIPT_DIR}/../monitor-app/docker-compose.yml" ]; then
        cp "${SCRIPT_DIR}/../monitor-app/docker-compose.yml" "${APP_DIR}/docker-compose.yml"
    else
        curl -fsSL "$RAW_COMPOSE_URL" -o "${APP_DIR}/docker-compose.yml"
    fi
fi

cd "$APP_DIR"
docker compose pull --quiet || docker compose pull
docker compose up -d --remove-orphans