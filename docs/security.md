# Security & Hardening Profile

This document details the security principles applied across `monitor-app`, Docker containerization, and token hygiene.

---

## 1. Container Hardening

The application container is built with defense-in-depth principles:

| Security Control | Implementation | Purpose |
| :--- | :--- | :--- |
| **Unprivileged User** | `USER 10001:10001` | Runs as a dedicated non-root `appuser` with no login shell (`/sbin/nologin`). |
| **Read-Only Root Filesystem** | `read_only: true` | Prevents runtime tampering or unauthorized file modifications. |
| **Capabilities Dropped** | `cap_drop: ["ALL"]` | Drops all Linux kernel capabilities. |
| **No Privilege Escalation** | `no-new-privileges:true` | Disables execution of `setuid` and `setgid` binaries. |
| **Ephemeral Scratchpad** | `tmpfs: ["/tmp:rw,noexec,nosuid,size=64m"]` | Restricts temporary storage to memory with execution disabled. |
| **Log Rotation** | `max-size: 10m, max-file: 3` | Protects the host system against disk exhaustion from runaway logs. |

---

## 2. Host Telemetry vs. Container Isolation

Because `monitor-app` monitors the host system (CPU, RAM, network rates, top host processes), it uses:
- `pid: host`
- `network_mode: host`

This allows `psutil` to inspect host metrics without requiring elevated privileges (`root` or `CAP_SYS_ADMIN`).

---

## 3. Token Hygiene & Secret Management

- **Push Token (Read & Write)**: Used strictly on developer workstations or GitHub Actions secrets to push images.
- **Deploy Token (Read-Only)**: Used strictly on production servers and EC2 instances to pull images without the ability to modify or delete repository artifacts.
- **Git Protection**: All tokens are stored locally in `.docker-tokens.env`, which is ignored by `.gitignore` to prevent secret exposure.
