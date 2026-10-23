"""Unit tests for metric and VPS scaling alert repository persistence."""

import json
import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, SystemMetricModel, VPSUsageAlertModel
from app.db.repository import persist_sample, persist_scaling_alert
from app.db.session import init_db


class TestDBRepository(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        init_db(self.engine)
        self.SessionFactory = sessionmaker(bind=self.engine)

    def test_persist_sample_normal(self):
        sample = {
            "ts": "2026-10-23T10:00:00+0000",
            "hostname": "test-host-01",
            "uptime_hours": 24.5,
            "ec2": {
                "instance_id": "i-1234567890abcdef0",
                "instance_type": "t3.micro",
                "availability_zone": "us-east-1a",
                "public_ip": "1.2.3.4",
            },
            "cpu": {
                "percent": 25.0,
                "cores": 2,
                "load_avg": [0.5, 0.4, 0.3],
            },
            "memory": {
                "percent": 45.0,
                "used_gb": 3.6,
                "total_gb": 8.0,
            },
            "swap": {
                "percent": 0.0,
                "used_gb": 0.0,
            },
            "disks": [
                {"mount": "/", "percent": 50.0, "total_gb": 40.0}
            ],
            "disk_io": {
                "read_mb_s": 0.1,
                "write_mb_s": 0.5,
            },
            "network_io": {
                "recv_mb_s": 0.2,
                "sent_mb_s": 0.3,
            },
            "top_cpu": [],
            "top_mem": [],
            "alerts": [],
        }

        success = persist_sample(self.SessionFactory, sample)
        self.assertTrue(success)

        session = self.SessionFactory()
        metric = session.query(SystemMetricModel).first()
        self.assertIsNotNone(metric)
        self.assertEqual(metric.hostname, "test-host-01")
        self.assertEqual(metric.instance_id, "i-1234567890abcdef0")
        self.assertEqual(metric.cpu_percent, 25.0)
        self.assertEqual(metric.load_avg_1m, 0.5)

        # No alerts should have been inserted
        alert_count = session.query(VPSUsageAlertModel).count()
        self.assertEqual(alert_count, 0)
        session.close()

    def test_persist_sample_with_scaling_alerts(self):
        sample = {
            "ts": "2026-10-23T10:15:00+0000",
            "hostname": "prod-vps-node",
            "uptime_hours": 120.0,
            "ec2": {
                "instance_id": "i-autoscaling99",
                "instance_type": "c5.xlarge",
                "availability_zone": "us-east-1b",
            },
            "cpu": {
                "percent": 96.5,
                "cores": 4,
                "load_avg": [8.2, 6.5, 4.1],
            },
            "memory": {
                "percent": 92.0,
                "used_gb": 14.8,
                "total_gb": 16.0,
            },
            "swap": {
                "percent": 15.0,
                "used_gb": 0.5,
            },
            "disks": [
                {"mount": "/", "percent": 75.0, "total_gb": 100.0}
            ],
            "disk_io": {"read_mb_s": 15.0, "write_mb_s": 25.0},
            "network_io": {"recv_mb_s": 10.0, "sent_mb_s": 20.0},
            "top_cpu": [
                {"pid": 1234, "name": "mysqld", "cpu_percent": 91.0, "memory_percent": 45.0}
            ],
            "top_mem": [
                {"pid": 1234, "name": "mysqld", "cpu_percent": 91.0, "memory_percent": 45.0}
            ],
            "alerts": [
                "CPU high: 96.5%",
                "Memory high: 92.0%",
            ],
        }

        success = persist_sample(self.SessionFactory, sample)
        self.assertTrue(success)

        session = self.SessionFactory()
        alerts = session.query(VPSUsageAlertModel).all()
        self.assertEqual(len(alerts), 2)

        cpu_alert = next(a for a in alerts if a.alert_type == "HIGH_CPU")
        self.assertEqual(cpu_alert.severity, "CRITICAL")
        self.assertEqual(cpu_alert.instance_id, "i-autoscaling99")
        self.assertIn("CPU high: 96.5%", cpu_alert.message)

        # Ensure top processes snapshot was serialized
        top_procs = json.loads(cpu_alert.top_cpu_processes)
        self.assertEqual(len(top_procs), 1)
        self.assertEqual(top_procs[0]["name"], "mysqld")
        session.close()

    def test_persist_scaling_alert_direct(self):
        alert_data = {
            "hostname": "node-scale-in",
            "instance_id": "i-scale1122",
            "alert_type": "SCALE_OUT_TRIGGERED",
            "severity": "WARNING",
            "message": "Autoscaling group triggered add instance due to sustained CPU > 85%",
            "cpu_percent": 89.0,
            "memory_percent": 82.0,
            "load_avg_1m": 4.5,
        }

        success = persist_scaling_alert(self.SessionFactory, alert_data)
        self.assertTrue(success)

        session = self.SessionFactory()
        saved = session.query(VPSUsageAlertModel).filter_by(instance_id="i-scale1122").first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.alert_type, "SCALE_OUT_TRIGGERED")
        self.assertEqual(saved.severity, "WARNING")
        session.close()


if __name__ == "__main__":
    unittest.main()
