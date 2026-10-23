"""Formatting and presentation functions for terminal and JSON output."""
import json


def print_report(s):
    """Print human-readable text report to standard output."""
    c, m = s["cpu"], s["memory"]
    print(f"\n=== {s['ts']}  {s['hostname']}  (up {s['uptime_hours']}h) ===")
    print(f"Public IP : {s.get('public_ip')}")
    print(f"Private IP: {s.get('private_ips')}")
    print(f"CPU       : {c['percent']}%  load {c['load_avg']}  cores {c['cores']}")
    print(f"Memory    : {m['percent']}%  ({m['used_gb']}/{m['total_gb']} GB)   Swap {s['swap']['percent']}%")
    for d in s.get("disks", []):
        print(f"Disk {d['mount']:<12}: {d['percent']}% of {d['total_gb']} GB")
    print(f"Disk I/O  : {s.get('disk_io')}")
    print(f"Network   : {s.get('network_io')}")
    print("Top CPU   :", ", ".join(f"{p['name']}({p['cpu_percent']}%)" for p in s.get("top_cpu", [])))
    print("Top MEM   :", ", ".join(f"{p['name']}({p['memory_percent']}%)" for p in s.get("top_mem", [])))


def format_json(s):
    """Serialize metrics dictionary to a JSON string."""
    return json.dumps(s)
