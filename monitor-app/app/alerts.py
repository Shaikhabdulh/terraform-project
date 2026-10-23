"""Threshold and alerting evaluation."""
from app.config import DEFAULT_SWAP_THRESHOLD


def check_thresholds(s, args):
    """Check metrics against configured alert thresholds and return alert messages."""
    alerts = []
    cpu_limit = getattr(args, "cpu", 85.0)
    mem_limit = getattr(args, "mem", 85.0)
    disk_limit = getattr(args, "disk", 85.0)
    swap_limit = getattr(args, "swap", DEFAULT_SWAP_THRESHOLD)

    if s["cpu"]["percent"] >= cpu_limit:
        alerts.append(f"CPU high: {s['cpu']['percent']}%")

    if s["memory"]["percent"] >= mem_limit:
        alerts.append(f"Memory high: {s['memory']['percent']}%")

    if s["swap"]["percent"] >= swap_limit:
        alerts.append(f"Swap in use: {s['swap']['percent']}%")

    for d in s.get("disks", []):
        if d["percent"] >= disk_limit:
            alerts.append(f"Disk {d['mount']} high: {d['percent']}%")

    cores = s["cpu"]["cores"] or 1
    if s["cpu"]["load_avg"][0] > cores * 2:
        alerts.append(f"Load average high: {s['cpu']['load_avg'][0]}")

    return alerts
