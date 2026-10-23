#!/usr/bin/env bash
#
# Automated deployment script for monitor-app container
#
set -euo pipefail

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_DIR="${REPO_ROOT}/monitor-app"

# ---- Pre-requisite checks ----------------------------------------------------
check_docker() {
    log "Checking Docker installation..."
    if ! command -v docker >/dev/null 2>&1; then
        die "Docker is not installed. Run 'bash ${SCRIPT_DIR}/install-docker.sh' first."
    fi

    if ! docker compose version >/dev/null 2>&1; then
        die "Docker Compose v2 is not installed. Run 'bash ${SCRIPT_DIR}/install-docker.sh' first."
    fi
}

# ---- Deploy monitor-app ------------------------------------------------------
deploy() {
    [ -d "$APP_DIR" ] || die "Directory not found: $APP_DIR"
    cd "$APP_DIR"

    log "Validating docker compose configuration..."
    docker compose config --quiet || die "Invalid docker compose configuration."

    log "Building and starting monitor-app container in secure mode..."
    docker compose up -d --build --remove-orphans

    log "Waiting for initial metric sampling..."
    sleep 3

    log "Verifying container status..."
    docker compose ps

    echo
    log "Recent output sample:"
    docker compose logs --tail 10

    echo
    log "Deployment successful!"
    echo "Useful commands:"
    echo "  Follow logs : cd $APP_DIR && docker compose logs -f"
    echo "  Stop monitor: cd $APP_DIR && docker compose down"
    echo "  Restart     : cd $APP_DIR && docker compose restart"
}

main() {
    check_docker
    deploy
}

main "$@"