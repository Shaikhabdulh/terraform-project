#!/usr/bin/env bash
#
# Non-interactive installer for Docker Engine + Docker Compose (v2 plugin)
# Supports: Ubuntu and Debian (amd64 / arm64)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/install-docker.sh | bash
#   or:  bash install-docker.sh
#
set -euo pipefail

# ---- Make every apt/dpkg step fully non-interactive -------------------------
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a          # don't prompt to restart services (Ubuntu 22.04+)
export NEEDRESTART_SUSPEND=1

APT_OPTS=(-y -qq
  -o Dpkg::Options::="--force-confdef"
  -o Dpkg::Options::="--force-confold")

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mWarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

main() {
    local SUDO="" TARGET_USER os_id codename arch

    # ---- Privileges ---------------------------------------------------------
    if [ "$(id -u)" -eq 0 ]; then
        TARGET_USER="${SUDO_USER:-root}"
    else
        command -v sudo >/dev/null 2>&1 || die "sudo is required when not running as root."
        sudo -n true 2>/dev/null || die "Passwordless sudo is required for non-interactive mode."
        SUDO="sudo"
        TARGET_USER="$(id -un)"
    fi

    # ---- OS detection -------------------------------------------------------
    [ -r /etc/os-release ] || die "Cannot detect OS (/etc/os-release missing)."
    # shellcheck disable=SC1091
    . /etc/os-release
    os_id="${ID:-}"
    codename="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"

    case "$os_id" in
        ubuntu|debian) ;;
        *) die "Unsupported OS '$os_id'. This script supports Ubuntu and Debian only." ;;
    esac
    [ -n "$codename" ] || die "Could not determine OS codename."
    arch="$(dpkg --print-architecture)"

    # ---- Skip if already installed -----------------------------------------
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        log "Docker and Docker Compose are already installed:"
        docker --version
        docker compose version
        log "Nothing to do."
        return 0
    fi

    # ---- Remove conflicting/unofficial packages ----------------------------
    log "Removing conflicting packages (if any)..."
    local pkg
    for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
        if dpkg -s "$pkg" >/dev/null 2>&1; then
            $SUDO apt-get remove "${APT_OPTS[@]}" "$pkg" >/dev/null
        fi
    done

    # ---- Prerequisites ------------------------------------------------------
    log "Installing prerequisites..."
    $SUDO apt-get update -qq
    $SUDO apt-get install "${APT_OPTS[@]}" ca-certificates curl >/dev/null

    # ---- Docker's official GPG key -----------------------------------------
    log "Adding Docker's official GPG key..."
    $SUDO install -m 0755 -d /etc/apt/keyrings
    $SUDO curl -fsSL "https://download.docker.com/linux/${os_id}/gpg" \
        -o /etc/apt/keyrings/docker.asc
    $SUDO chmod a+r /etc/apt/keyrings/docker.asc

    # ---- Docker apt repository (deb822 format) -----------------------------
    log "Adding Docker apt repository..."
    $SUDO rm -f /etc/apt/sources.list.d/docker.list   # avoid duplicate/old-style entry
    $SUDO tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/${os_id}
Suites: ${codename}
Components: stable
Architectures: ${arch}
Signed-By: /etc/apt/keyrings/docker.asc
EOF

    # ---- Install Docker Engine + Compose plugin ----------------------------
    log "Installing Docker Engine, Buildx and Compose plugin..."
    $SUDO apt-get update -qq
    $SUDO apt-get install "${APT_OPTS[@]}" \
        docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin >/dev/null

    # ---- Start on boot ------------------------------------------------------
    if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
        log "Enabling and starting Docker..."
        $SUDO systemctl enable --now docker containerd >/dev/null 2>&1
    else
        warn "systemd not detected; start Docker manually (e.g. 'sudo service docker start')."
    fi

    # ---- Allow non-root usage ----------------------------------------------
    if [ "$TARGET_USER" != "root" ]; then
        log "Adding '$TARGET_USER' to the docker group..."
        $SUDO usermod -aG docker "$TARGET_USER"
    fi

    # ---- Verify -------------------------------------------------------------
    log "Verifying installation..."
    $SUDO docker --version
    $SUDO docker compose version
    if $SUDO docker run --rm hello-world >/dev/null 2>&1; then
        log "hello-world container ran successfully."
    else
        warn "hello-world test failed. Check: sudo systemctl status docker"
    fi

    echo
    log "Done."
    if [ "$TARGET_USER" != "root" ]; then
        echo "Log out and back in (or run 'newgrp docker') to use docker without sudo."
    fi
}

main "$@"