#!/usr/bin/env bash
#
# Non-interactive Build and Push script for sah1/practice:monitor-app
#
set -euo pipefail

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_DIR="${REPO_ROOT}/monitor-app"

IMAGE_TAG="${IMAGE_TAG:-sah1/practice:monitor-app}"
DOCKER_USER="${DOCKER_USER:-sah1}"
DOCKER_PUSH_TOKEN="${1:-${DOCKER_PUSH_TOKEN:-}}"

if [ -z "$DOCKER_PUSH_TOKEN" ]; then
    die "Push token required. Usage: $0 <DOCKER_PUSH_TOKEN> or export DOCKER_PUSH_TOKEN='...'"
fi

log "Authenticating with Docker Hub non-interactively as '${DOCKER_USER}'..."
echo "$DOCKER_PUSH_TOKEN" | docker login -u "$DOCKER_USER" --password-stdin

log "Building '${IMAGE_TAG}' from ${APP_DIR}..."
docker build -t "$IMAGE_TAG" "$APP_DIR"

log "Pushing '${IMAGE_TAG}' to Docker Hub..."
docker push "$IMAGE_TAG"

echo
log "Successfully pushed ${IMAGE_TAG} to Docker Hub!"