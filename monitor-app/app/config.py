"""Configuration and constants for the monitor application."""
import logging

IMDS_BASE = "http://169.254.169.254/latest"
PUBLIC_IP_FALLBACK = "https://checkip.amazonaws.com"
HTTP_TIMEOUT = 2  # seconds

DEFAULT_INTERVAL = 10
DEFAULT_CPU_THRESHOLD = 85.0
DEFAULT_MEM_THRESHOLD = 85.0
DEFAULT_DISK_THRESHOLD = 85.0
DEFAULT_SWAP_THRESHOLD = 50.0

log = logging.getLogger("sysmon")


def setup_logging(level=logging.INFO):
    """Configure standard logging for the monitor application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s"
    )
