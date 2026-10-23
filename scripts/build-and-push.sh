#!/usr/bin/env bash
#
# Minimal build and push script for sah1/practice:monitor-app
#
set -euo pipefail

DOCKER_USER="${DOCKER_USER:-sah1}"
DOCKER_PUSH_TOKEN="${1:-${DOCKER_PUSH_TOKEN:-}}"
IMAGE_TAG="${IMAGE_TAG:-sah1/practice:monitor-app}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/../monitor-app"

if [ -z "$DOCKER_PUSH_TOKEN" ]; then
    echo "Error: DOCKER_PUSH_TOKEN required. Usage: $0 <token>" >&2
    exit 1
fi

echo "$DOCKER_PUSH_TOKEN" | docker login -u "$DOCKER_USER" --password-stdin
docker build -t "$IMAGE_TAG" "$APP_DIR"
docker push "$IMAGE_TAG"