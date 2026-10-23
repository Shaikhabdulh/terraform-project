#!/usr/bin/env bash
#
# Non-interactive automated deployer for monitor-app container
# Pulls sah1/practice:monitor-app from Docker Hub and runs in hardened secure mode.
#
# Usage:
#   bash scripts/deploy-monitor.sh [--token <PAT>]
#   curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/deploy-monitor.sh | bash -s -- [--token <PAT>]
#
set -euo pipefail

# Non-interactive environment guards
export DEBIAN_FRONTEND=noninteractive

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

# GitHub raw URL for remote standalone execution
RAW_COMPOSE_URL="https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/monitor-app/docker-compose.yml"

# Locate repo directory or fallback to standalone working directory
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
    APP_DIR="${REPO_ROOT}/monitor-app"
else
    APP_DIR="${PWD}/monitor-app"
fi

# Defaults
DOCKER_USER="sah1"
DOCKER_PAT="${DOCKER_PAT:-}"
SKIP_LOGIN=false

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Non-interactive Options:
  -t, --token, --pat <TOKEN>   Docker Hub Personal Access Token (or set DOCKER_PAT env var)
  -u, --user <USERNAME>        Docker Hub username (default: sah1)
  --no-login                   Skip docker login before pulling
  -h, --help                   Show this help message
EOF
    exit 0
}

# Parse command line options non-interactively
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--token|--pat)
            DOCKER_PAT="$2"
            shift 2
            ;;
        -u|--user)
            DOCKER_USER="$2"
            shift 2
            ;;
        --no-login)
            SKIP_LOGIN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            warn "Unknown argument: $1 (ignoring for non-interactive execution)"
            shift
            ;;
    esac
done

# ---- Pre-requisite checks ----------------------------------------------------
check_docker() {
    log "Checking Docker installation..."
    if ! command -v docker >/dev/null 2>&1; then
        die "Docker is not installed. Install Docker first using: curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/install-docker.sh | bash"
    fi

    if ! docker compose version >/dev/null 2>&1; then
        die "Docker Compose v2 plugin is not installed."
    fi
}

# ---- Prepare Compose File ----------------------------------------------------
prepare_app_dir() {
    mkdir -p "$APP_DIR"
    if [ ! -f "${APP_DIR}/docker-compose.yml" ]; then
        log "Fetching docker-compose.yml from repository..."
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "$RAW_COMPOSE_URL" -o "${APP_DIR}/docker-compose.yml"
        elif command -v wget >/dev/null 2>&1; then
            wget -qO "${APP_DIR}/docker-compose.yml" "$RAW_COMPOSE_URL"
        else
            die "Neither curl nor wget is available to fetch docker-compose.yml."
        fi
    fi
}

# ---- Authenticate with Docker Hub Non-Interactively --------------------------
docker_login() {
    if [ "$SKIP_LOGIN" = true ]; then
        log "Skipping Docker Hub authentication (--no-login)."
        return 0
    fi

    if [ -n "$DOCKER_PAT" ]; then
        log "Authenticating with Docker Hub non-interactively as '${DOCKER_USER}'..."
        echo "$DOCKER_PAT" | docker login -u "$DOCKER_USER" --password-stdin >/dev/null 2>&1 || {
            warn "Docker login failed. Proceeding with anonymous pull..."
        }
    else
        log "No PAT provided; proceeding with anonymous pull..."
    fi
}

# ---- Deploy monitor-app Non-Interactively ------------------------------------
deploy() {
    cd "$APP_DIR"

    log "Validating docker-compose.yml configuration..."
    docker compose config --quiet || die "Invalid docker compose configuration."

    log "Pulling image 'sah1/practice:monitor-app' from Docker Hub non-interactively..."
    docker compose pull --quiet || docker compose pull

    log "Starting monitor-app container in secure mode..."
    docker compose up -d --remove-orphans

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
    prepare_app_dir
    docker_login
    deploy
}

main "$@"