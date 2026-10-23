# Monitor App (`monitor-app`)

A modular system and AWS EC2 resource monitoring toolkit for Linux and cloud instances, rewritten and organized into clean, reusable packages.

---

## Features

- **Network & Identity**:
  - Automatically queries AWS IMDSv2 metadata (`instance-id`, `instance-type`, `availability-zone`, `mac`, `local-ipv4`) without requiring credentials or the AWS SDK (`boto3`).
  - Resolves non-loopback local private IP addresses per network interface.
  - Resolves public IP via IMDSv2 or falls back gracefully to `checkip.amazonaws.com`.
  - Alerts automatically on public IP address changes (e.g. EC2 stop/restart without Elastic IP).
- **Resource Metrics Collection**:
  - CPU usage (overall percent + per-core breakdown).
  - System load averages (1, 5, 15 minutes) with cross-platform fallback.
  - Memory & Swap usage (percentages, total, used, available in GB).
  - Disk filesystem usage per mount point, plus live disk I/O read/write transfer rates (MB/s).
  - Network I/O transfer rates (MB/s in/out), errors, and drops.
  - Top 5 processes sorted by CPU and Memory usage.
- **Alerting & Thresholds**:
  - Configurable alert limits for CPU, memory, swap, disk partitions, and high load averages.
- **Reporting & Telemetry**:
  - Formatted terminal dashboard output.
  - Streamable single-line JSON format (ideal for CloudWatch Agent, Vector, Fluent Bit, Loki, or ELK stack).

---

## Project Structure

```text
monitor-app/
├── pyproject.toml        # Build metadata & entry-points
├── requirements.txt      # Dependencies (psutil)
├── README.md             # Documentation & deployment guide
├── main.py               # Root runner script
├── app/                  # Main package
│   ├── __init__.py       # Package exports
│   ├── __main__.py       # Module entry point (python -m app)
│   ├── config.py         # Config constants, defaults, and logging
│   ├── identity.py       # AWS IMDSv2 metadata & IP resolution
│   ├── collector.py      # Resource metric collection engine
│   ├── alerts.py         # Alerting logic and threshold checks
│   ├── reporter.py       # Terminal & JSON reporting formatters
│   └── cli.py            # CLI parser, signal handling, and main loop
└── tests/                # Unit tests
    ├── __init__.py
    ├── test_alerts.py
    ├── test_collector.py
    ├── test_identity.py
    └── test_reporter.py
```

---

## Installation

### Prerequisites
- Python 3.9+
- `psutil>=5.9.0`

### Setup

```bash
cd monitor-app
pip install -r requirements.txt
```

Or using `uv`:

```bash
cd monitor-app
uv pip install -r requirements.txt
```

---

## Usage

### 1. Run via root runner:
```bash
python main.py
```

### 2. Run as Python module:
```bash
python -m app --interval 10
```

### 3. Run once and exit:
```bash
python main.py --once
```

### 4. Output JSON lines for log aggregators (CloudWatch, Loki, ELK):
```bash
python main.py --json >> /var/log/sysmon.log
```

### 5. Custom Alert Thresholds:
```bash
python main.py --cpu 90 --mem 80 --disk 85 --interval 15
```

---

## Docker & Docker Compose (Secure Mode)

The application is fully containerized and pre-configured to monitor the host system securely:

### 1. One-Command Non-Interactive Deploy (via script)
```bash
bash ../scripts/deploy-monitor.sh
```

Or standalone via remote pipe (no clone needed):
```bash
curl -fsSL https://raw.githubusercontent.com/Shaikhabdulh/terraform-project/main/scripts/deploy-monitor.sh | bash
```

### 2. Manual Docker Compose
```bash
cd monitor-app

# Pull published image from Docker Hub
docker compose pull

# Start container in background (secure mode)
docker compose up -d

# View real-time streaming JSON logs
docker compose logs -f

# Check container health and status
docker compose ps

# Stop the container
docker compose down
```

### Security Hardening Profile
- **Unprivileged User**: Runs as non-root `appuser` (UID/GID `10001:10001`).
- **Read-Only Root Filesystem**: `read_only: true` prevents runtime filesystem tampering.
- **Dropped Capabilities**: `cap_drop: [ALL]` drops all Linux capabilities.
- **No Privilege Escalation**: `no-new-privileges:true` prevents `setuid`/`setgid` binary execution.
- **Ephemeral Scratchpad**: Restricted `tmpfs` mounted at `/tmp` (`noexec,nosuid`).
- **Host Namespace Telemetry**: Uses `pid: host` and `network_mode: host` to inspect host metrics without needing root privileges.
- **Log Rotation**: Capped at 3 files of 10MB each (`json-file`) to prevent host disk exhaustion.

---

## Systemd Service Configuration (Linux / EC2)

Create `/etc/systemd/system/sysmon.service`:

```ini
[Unit]
Description=System & Resource Monitor Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=nobody
WorkingDirectory=/opt/monitor-app
ExecStart=/usr/bin/python3 -m app --json --interval 30
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sysmon
sudo journalctl -u sysmon -f
```
