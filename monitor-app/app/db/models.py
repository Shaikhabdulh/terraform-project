"""SQLAlchemy ORM models for system telemetry and VPS scaling alerts."""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SystemMetricModel(Base):
    """Stores regular heartbeat system metrics for EC2 / VPS instances."""

    __tablename__ = "system_metrics"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    hostname = Column(String(255), nullable=False, index=True)
    instance_id = Column(String(100), nullable=True, index=True)
    instance_type = Column(String(50), nullable=True)
    availability_zone = Column(String(50), nullable=True)
    public_ip = Column(String(50), nullable=True)

    uptime_hours = Column(Float, nullable=True)
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    swap_percent = Column(Float, nullable=True)

    load_avg_1m = Column(Float, nullable=True)
    load_avg_5m = Column(Float, nullable=True)
    load_avg_15m = Column(Float, nullable=True)

    disk_usage_percent = Column(Float, nullable=True)
    disk_read_mb_s = Column(Float, nullable=True)
    disk_write_mb_s = Column(Float, nullable=True)
    net_recv_mb_s = Column(Float, nullable=True)
    net_sent_mb_s = Column(Float, nullable=True)

    raw_payload = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<SystemMetric(id={self.id}, host='{self.hostname}', "
            f"cpu={self.cpu_percent}%, mem={self.memory_percent}%)>"
        )


class VPSUsageAlertModel(Base):
    """Stores high utilization and auto-scaling events for VPS / EC2 audit and web display.

    Records spike conditions (CPU > threshold, Memory > threshold, load spikes) along with
    a full snapshot of the top resource-consuming processes at that exact instant.
    This enables long-term autoscaling analysis, root cause forensics, and web dashboard alerts.
    """

    __tablename__ = "vps_scaling_alerts"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    hostname = Column(String(255), nullable=False, index=True)
    instance_id = Column(String(100), nullable=True, index=True)
    instance_type = Column(String(50), nullable=True)
    availability_zone = Column(String(50), nullable=True)

    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="WARNING", index=True)
    message = Column(Text, nullable=False)

    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    swap_percent = Column(Float, nullable=True)
    load_avg_1m = Column(Float, nullable=True)
    load_avg_5m = Column(Float, nullable=True)

    # JSON snapshot of top processes consuming CPU and RAM at the spike moment
    top_cpu_processes = Column(Text, nullable=True)
    top_mem_processes = Column(Text, nullable=True)

    resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<VPSUsageAlert(id={self.id}, type='{self.alert_type}', "
            f"severity='{self.severity}', host='{self.hostname}')>"
        )
