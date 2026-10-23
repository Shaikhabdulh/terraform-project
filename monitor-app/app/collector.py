"""Resource metrics collection for CPU, memory, swap, disk, network, and processes."""
import os
import socket
import time
import psutil


def get_load_average():
    """Return 1, 5, and 15 minute load averages, with fallback for non-POSIX platforms."""
    if hasattr(os, "getloadavg"):
        try:
            return os.getloadavg()
        except OSError:
            pass
    # Fallback on platforms without os.getloadavg (such as Windows)
    cpu_p = psutil.cpu_percent(interval=None)
    fake_load = round(cpu_p / 100.0 * (psutil.cpu_count() or 1), 2)
    return (fake_load, fake_load, fake_load)


class Collector:
    """Keeps previous counters so we can report per-second rates."""

    def __init__(self):
        self._prev_t = time.monotonic()
        self._prev_disk = psutil.disk_io_counters()
        self._prev_net = psutil.net_io_counters()
        psutil.cpu_percent(percpu=True)  # prime (first call always returns 0)
        for p in psutil.process_iter():  # prime per-process cpu counters
            try:
                p.cpu_percent(None)
            except psutil.Error:
                pass

    def sample(self):
        """Sample all resource counters and calculate per-second rates."""
        now = time.monotonic()
        dt = max(now - self._prev_t, 1e-6)

        disk = psutil.disk_io_counters()
        net = psutil.net_io_counters()

        disk_rate = {
            "read_mb_s": 0.0,
            "write_mb_s": 0.0,
        }
        if disk and self._prev_disk:
            disk_rate["read_mb_s"] = round((disk.read_bytes - self._prev_disk.read_bytes) / dt / 1e6, 3)
            disk_rate["write_mb_s"] = round((disk.write_bytes - self._prev_disk.write_bytes) / dt / 1e6, 3)

        net_rate = {
            "recv_mb_s": 0.0,
            "sent_mb_s": 0.0,
            "errors_in": 0,
            "errors_out": 0,
            "drops_in": 0,
            "drops_out": 0,
        }
        if net and self._prev_net:
            net_rate["recv_mb_s"] = round((net.bytes_recv - self._prev_net.bytes_recv) / dt / 1e6, 3)
            net_rate["sent_mb_s"] = round((net.bytes_sent - self._prev_net.bytes_sent) / dt / 1e6, 3)
            net_rate["errors_in"] = net.errin
            net_rate["errors_out"] = net.errout
            net_rate["drops_in"] = net.dropin
            net_rate["drops_out"] = net.dropout

        self._prev_t, self._prev_disk, self._prev_net = now, disk, net

        per_cpu = psutil.cpu_percent(percpu=True)
        avg_cpu = round(sum(per_cpu) / len(per_cpu), 1) if per_cpu else 0.0
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        load1, load5, load15 = get_load_average()

        disks = []
        for part in psutil.disk_partitions(all=False):
            if "loop" in part.device or part.fstype in ("squashfs", "overlay"):
                continue
            try:
                u = psutil.disk_usage(part.mountpoint)
            except OSError:
                continue
            disks.append({
                "mount": part.mountpoint,
                "total_gb": round(u.total / 1e9, 1),
                "percent": u.percent
            })

        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                procs.append(p.info)
            except psutil.Error:
                pass

        top_cpu = sorted(procs, key=lambda x: x.get("cpu_percent") or 0, reverse=True)[:5]
        top_mem = sorted(procs, key=lambda x: x.get("memory_percent") or 0, reverse=True)[:5]
        for lst in (top_cpu, top_mem):
            for p in lst:
                p["cpu_percent"] = round(p.get("cpu_percent") or 0, 1)
                p["memory_percent"] = round(p.get("memory_percent") or 0, 1)

        return {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "hostname": socket.gethostname(),
            "uptime_hours": round((time.time() - psutil.boot_time()) / 3600, 1),
            "cpu": {
                "percent": avg_cpu,
                "per_core": per_cpu,
                "cores": psutil.cpu_count(),
                "load_avg": [round(load1, 2), round(load5, 2), round(load15, 2)],
            },
            "memory": {
                "percent": vm.percent,
                "used_gb": round(vm.used / 1e9, 2),
                "total_gb": round(vm.total / 1e9, 2),
                "available_gb": round(vm.available / 1e9, 2),
            },
            "swap": {
                "percent": sw.percent,
                "used_gb": round(sw.used / 1e9, 2)
            },
            "disks": disks,
            "disk_io": disk_rate,
            "network_io": net_rate,
            "top_cpu": top_cpu,
            "top_mem": top_mem,
        }
