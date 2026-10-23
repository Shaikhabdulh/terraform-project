"""Network identity, IP resolution, and AWS EC2 IMDSv2 metadata helpers."""
import socket
import urllib.error
import urllib.request
import psutil

from app.config import HTTP_TIMEOUT, IMDS_BASE, PUBLIC_IP_FALLBACK


def _http(url, method="GET", headers=None, timeout=HTTP_TIMEOUT):
    """Perform a simple HTTP request with timeout."""
    req = urllib.request.Request(url, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode().strip()


_imds_available = None


def reset_imds_cache():
    """Reset IMDS availability cache (useful for testing or network changes)."""
    global _imds_available
    _imds_available = None


def _get_imds_token():
    """Retrieve IMDSv2 session token, caching whether IMDS is reachable."""
    global _imds_available
    if _imds_available is False:
        return None
    try:
        token = _http(
            f"{IMDS_BASE}/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "300"},
            timeout=1,
        )
        _imds_available = True
        return token
    except (urllib.error.URLError, OSError):
        _imds_available = False
        return None


def imds_get(path):
    """Read a value from the EC2 metadata service (IMDSv2). Returns None if unavailable."""
    token = _get_imds_token()
    if not token:
        return None
    try:
        return _http(f"{IMDS_BASE}/meta-data/{path}", headers={"X-aws-ec2-metadata-token": token})
    except (urllib.error.URLError, OSError):
        return None


def get_public_ip():
    """Public IP: IMDS first (no internet call), then checkip.amazonaws.com."""
    ip = imds_get("public-ipv4")
    if ip:
        return ip
    try:
        return _http(PUBLIC_IP_FALLBACK)
    except (urllib.error.URLError, OSError):
        return None


def get_private_ips():
    """All non-loopback IPv4 addresses per interface, read straight from the OS."""
    result = {}
    for iface, addrs in psutil.net_if_addrs().items():
        ips = [a.address for a in addrs if a.family == socket.AF_INET and not a.address.startswith("127.")]
        if ips:
            result[iface] = ips
    return result


def get_instance_info():
    """Static info; fetched once at startup. Empty values if not on EC2."""
    keys = {
        "instance_id": "instance-id",
        "instance_type": "instance-type",
        "availability_zone": "placement/availability-zone",
        "private_ip_imds": "local-ipv4",
        "mac": "mac",
    }
    return {name: imds_get(path) for name, path in keys.items()}
