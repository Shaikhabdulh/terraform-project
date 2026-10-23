"""Command-line interface and main monitoring event loop."""
import argparse
import logging
import os
import platform
import signal
import sys
import time

from app.alerts import check_thresholds
from app.collector import Collector
from app.config import (
    DEFAULT_CPU_THRESHOLD,
    DEFAULT_DISK_THRESHOLD,
    DEFAULT_INTERVAL,
    DEFAULT_MEM_THRESHOLD,
    setup_logging,
)
from app.db.config import get_db_settings
from app.db.repository import persist_sample
from app.db.session import create_db_engine, get_session_factory, init_db
from app.identity import get_instance_info, get_private_ips, get_public_ip
from app.reporter import format_json, print_report

log = logging.getLogger("sysmon")


def build_parser():
    """Construct command-line argument parser with environment variable defaults."""
    env_interval = int(os.environ.get("SYSMON_INTERVAL", DEFAULT_INTERVAL))
    env_cpu = float(os.environ.get("SYSMON_CPU_THRESHOLD", DEFAULT_CPU_THRESHOLD))
    env_mem = float(os.environ.get("SYSMON_MEM_THRESHOLD", DEFAULT_MEM_THRESHOLD))
    env_disk = float(os.environ.get("SYSMON_DISK_THRESHOLD", DEFAULT_DISK_THRESHOLD))
    env_json = os.environ.get("SYSMON_JSON", "false").lower() in ("true", "1", "yes")

    ap = argparse.ArgumentParser(description="Simple Linux/AWS system monitor")
    ap.add_argument(
        "--interval",
        type=int,
        default=env_interval,
        help=f"Seconds between samples (default: {DEFAULT_INTERVAL})",
    )
    ap.add_argument(
        "--once",
        action="store_true",
        help="Print one sample and exit",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        default=env_json,
        help="Emit one JSON line per sample",
    )
    ap.add_argument(
        "--cpu",
        type=float,
        default=env_cpu,
        help=f"CPU alert threshold %% (default: {DEFAULT_CPU_THRESHOLD})",
    )
    ap.add_argument(
        "--mem",
        type=float,
        default=env_mem,
        help=f"Memory alert threshold %% (default: {DEFAULT_MEM_THRESHOLD})",
    )
    ap.add_argument(
        "--disk",
        type=float,
        default=env_disk,
        help=f"Disk alert threshold %% (default: {DEFAULT_DISK_THRESHOLD})",
    )
    return ap


def main(argv=None):
    """Main monitor execution loop."""
    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging()

    # Initialize database if credentials are configured (AWS Secrets Manager or .env)
    session_factory = None
    try:
        db_settings = get_db_settings()
        if db_settings:
            engine = create_db_engine(db_settings)
            init_db(engine)
            session_factory = get_session_factory(engine)
            log.info(
                "Database configured: connected to %s:%s/%s",
                db_settings.host,
                db_settings.port,
                db_settings.database,
            )
    except Exception as exc:
        log.warning("Database initialization skipped or failed: %s", exc)
        session_factory = None

    running = True

    def stop(*_):
        nonlocal running
        running = False

    try:
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
    except (ValueError, AttributeError):
        pass  # SIGTERM may not be supported on all environments/threads

    info = get_instance_info()
    if not args.json:
        print(f"Host: {platform.node()} | {platform.platform()}")
        print(f"AWS : {info}")

    collector = Collector()
    last_public_ip = None
    time.sleep(1)  # let initial rate window accumulate

    while running:
        s = collector.sample()
        s["public_ip"] = get_public_ip()
        s["private_ips"] = get_private_ips()
        s["instance"] = info

        if last_public_ip and s["public_ip"] and s["public_ip"] != last_public_ip:
            log.warning("PUBLIC IP CHANGED: %s -> %s", last_public_ip, s["public_ip"])
        if s["public_ip"]:
            last_public_ip = s["public_ip"]

        s["alerts"] = check_thresholds(s, args)
        for a in s["alerts"]:
            log.warning("ALERT: %s", a)

        if session_factory:
            try:
                persist_sample(session_factory, s)
            except Exception as exc:
                log.warning("Failed to persist sample to database: %s", exc)

        if args.json:
            print(format_json(s), flush=True)
        else:
            print_report(s)

        if args.once:
            break

        # Sleep in 1-second slices for responsive termination
        for _ in range(args.interval):
            if not running:
                break
            time.sleep(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
