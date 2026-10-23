"""Data access and persistence service for metrics and VPS scaling alerts."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.db.models import SystemMetricModel, VPSUsageAlertModel

logger = logging.getLogger("sysmon.db")


def _parse_timestamp(ts: Optional[str]) -> datetime:
    """Parse an ISO timestamp or return current UTC time."""
    if not ts:
        return datetime.now(timezone.utc)
    try:
        # Replace "+0000" or similar trailing formats if necessary
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def _classify_alert(alert_msg: str) -> str:
    """Classify the alert type based on alert text content."""
    upper = alert_msg.upper()
    if "CPU" in upper:
        return "HIGH_CPU"
    if "MEMORY" in upper or "MEM" in upper:
        return "HIGH_MEMORY"
    if "SWAP" in upper:
        return "HIGH_SWAP"
    if "DISK" in upper:
        return "HIGH_DISK"
    if "LOAD" in upper:
        return "HIGH_LOAD"
    return "SYSTEM_ALERT"


def persist_sample(session_factory: sessionmaker, sample: Dict[str, Any]) -> bool:
    """Persist a single resource sample to the database.

    Persists:
    1. Regular heartbeat metrics to `system_metrics`.
    2. High VPS usage alerts and scaling triggers to `vps_scaling_alerts` if thresholds are exceeded.

    Returns True if successfully written, or False if persistence failed.
    Never raises an uncaught database error to ensure the monitoring loop continues running.
    """
    session = session_factory()
    try:
        dt = _parse_timestamp(sample.get("ts"))
        hostname = sample.get("hostname", "unknown")
        ec2 = sample.get("ec2") or sample.get("instance") or {}
        public_ip = ec2.get("public_ip") or sample.get("public_ip")
        cpu = sample.get("cpu") or {}
        mem = sample.get("memory") or {}
        swap = sample.get("swap") or {}
        disks = sample.get("disks") or []
        disk_io = sample.get("disk_io") or {}
        net_io = sample.get("network_io") or {}

        load_avg = cpu.get("load_avg") or []
        load_1m = load_avg[0] if len(load_avg) > 0 else None
        load_5m = load_avg[1] if len(load_avg) > 1 else None
        load_15m = load_avg[2] if len(load_avg) > 2 else None

        disk_pct = disks[0].get("percent") if disks else None

        # 1. Heartbeat metric record
        metric_record = SystemMetricModel(
            timestamp=dt,
            hostname=hostname,
            instance_id=ec2.get("instance_id"),
            instance_type=ec2.get("instance_type"),
            availability_zone=ec2.get("availability_zone"),
            public_ip=public_ip,
            uptime_hours=sample.get("uptime_hours"),
            cpu_percent=float(cpu.get("percent", 0.0)),
            memory_percent=float(mem.get("percent", 0.0)),
            swap_percent=float(swap.get("percent", 0.0)) if "percent" in swap else None,
            load_avg_1m=load_1m,
            load_avg_5m=load_5m,
            load_avg_15m=load_15m,
            disk_usage_percent=disk_pct,
            disk_read_mb_s=disk_io.get("read_mb_s"),
            disk_write_mb_s=disk_io.get("write_mb_s"),
            net_recv_mb_s=net_io.get("recv_mb_s"),
            net_sent_mb_s=net_io.get("sent_mb_s"),
            raw_payload=json.dumps(sample),
        )
        session.add(metric_record)

        # 2. Check for alerts / scaling events
        alerts = sample.get("alerts") or []
        if alerts:
            top_cpu_json = json.dumps(sample.get("top_cpu") or [])
            top_mem_json = json.dumps(sample.get("top_mem") or [])
            cpu_val = float(cpu.get("percent", 0.0))
            mem_val = float(mem.get("percent", 0.0))

            for alert_msg in alerts:
                alert_type = _classify_alert(alert_msg)
                severity = "CRITICAL" if (cpu_val >= 90.0 or mem_val >= 90.0) else "WARNING"

                alert_record = VPSUsageAlertModel(
                    timestamp=dt,
                    hostname=hostname,
                    instance_id=ec2.get("instance_id"),
                    instance_type=ec2.get("instance_type"),
                    availability_zone=ec2.get("availability_zone"),
                    alert_type=alert_type,
                    severity=severity,
                    message=alert_msg,
                    cpu_percent=cpu_val,
                    memory_percent=mem_val,
                    swap_percent=float(swap.get("percent", 0.0)) if "percent" in swap else None,
                    load_avg_1m=load_1m,
                    load_avg_5m=load_5m,
                    top_cpu_processes=top_cpu_json,
                    top_mem_processes=top_mem_json,
                    resolved=False,
                )
                session.add(alert_record)

        session.commit()
        return True

    except SQLAlchemyError as err:
        logger.warning(f"Database persistence error: {err}")
        session.rollback()
        return False
    except Exception as err:
        logger.error(f"Unexpected error persisting metrics: {err}")
        session.rollback()
        return False
    finally:
        session.close()


def persist_scaling_alert(session_factory: sessionmaker, alert_data: Dict[str, Any]) -> bool:
    """Directly persist a specific VPS scaling alert event.

    Useful for external autoscaling triggers, lifecycle hooks, or manual threshold alerts.
    """
    session = session_factory()
    try:
        dt = alert_data.get("timestamp")
        if isinstance(dt, str):
            dt = _parse_timestamp(dt)
        elif not isinstance(dt, datetime):
            dt = datetime.now(timezone.utc)

        alert = VPSUsageAlertModel(
            timestamp=dt,
            hostname=alert_data.get("hostname", "unknown"),
            instance_id=alert_data.get("instance_id"),
            instance_type=alert_data.get("instance_type"),
            availability_zone=alert_data.get("availability_zone"),
            alert_type=alert_data.get("alert_type", "SCALING_EVENT"),
            severity=alert_data.get("severity", "WARNING"),
            message=alert_data.get("message", "High resource scaling trigger"),
            cpu_percent=float(alert_data.get("cpu_percent", 0.0)),
            memory_percent=float(alert_data.get("memory_percent", 0.0)),
            swap_percent=float(alert_data.get("swap_percent", 0.0)),
            load_avg_1m=alert_data.get("load_avg_1m"),
            load_avg_5m=alert_data.get("load_avg_5m"),
            top_cpu_processes=json.dumps(alert_data.get("top_cpu_processes") or []),
            top_mem_processes=json.dumps(alert_data.get("top_mem_processes") or []),
            resolved=alert_data.get("resolved", False),
        )
        session.add(alert)
        session.commit()
        return True

    except SQLAlchemyError as err:
        logger.warning(f"Error persisting scaling alert: {err}")
        session.rollback()
        return False
    except Exception as err:
        logger.error(f"Unexpected error persisting scaling alert: {err}")
        session.rollback()
        return False
    finally:
        session.close()
