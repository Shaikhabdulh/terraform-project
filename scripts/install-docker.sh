#!/usr/bin/env bash
#
# Minimal unattended Docker Engine + Compose v2 installer for Ubuntu/Debian
#
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
export NEEDRESTART_SUSPEND=1

APT_OPTS=(-y -qq -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold")

# Exit if already installed
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    exit 0
fi

# Detect root / sudo
SUDO=""
TARGET_USER="$(id -un)"
if [ "$(id -u)" -ne 0 ]; then
    command -v sudo >/dev/null 2>&1 || { echo "Error: sudo required" >&2; exit 1; }
    SUDO="sudo"
fi

. /etc/os-release
case "${ID:-}" in
    ubuntu|debian) ;;
    *) echo "Error: Unsupported OS '$ID'" >&2; exit 1 ;;
esac

codename="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"
arch="$(dpkg --print-architecture)"

# Remove old/conflicting packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    if dpkg -s "$pkg" >/dev/null 2>&1; then
        $SUDO apt-get remove "${APT_OPTS[@]}" "$pkg" >/dev/null 2>&1 || true
    fi
done

# Prerequisites
$SUDO apt-get update -qq
$SUDO apt-get install "${APT_OPTS[@]}" ca-certificates curl >/dev/null

# Docker GPG key & deb822 repo
$SUDO install -m 0755 -d /etc/apt/keyrings
$SUDO curl -fsSL "https://download.docker.com/linux/${ID}/gpg" -o /etc/apt/keyrings/docker.asc
$SUDO chmod a+r /etc/apt/keyrings/docker.asc

$SUDO rm -f /etc/apt/sources.list.d/docker.list
$SUDO tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/${ID}
Suites: ${codename}
Components: stable
Architectures: ${arch}
Signed-By: /etc/apt/keyrings/docker.asc
EOF

# Install Docker packages
$SUDO apt-get update -qq
$SUDO apt-get install "${APT_OPTS[@]}" docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null

# Enable and start service
if command -v systemctl >/dev/null 2>&1; then
    $SUDO systemctl enable --now docker containerd >/dev/null 2>&1 || true
fi

# Add current user to docker group if non-root
if [ "$TARGET_USER" != "root" ]; then
    $SUDO usermod -aG docker "$TARGET_USER" || true
fi