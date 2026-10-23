import json
import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, SystemMetricModel, VPSUsageAlertModel
from app.db.session import init_db


class TestDBModels(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        init_db(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def test_create_system_metric_record(self):
        session = self.Session()
        now = datetime.now(timezone.utc)
        record = SystemMetricModel(
            timestamp=now,
            hostname="web-node-01",
            instance_id="i-0abc1234def567890",
            instance_type="t3.medium",
            availability_zone="us-east-1a",
            public_ip="54.210.1.2",
            uptime_hours=48.2,
            cpu_percent=45.5,
            memory_percent=60.2,
            swap_percent=0.0,
            load_avg_1m=1.2,
            load_avg_5m=1.0,
            load_avg_15m=0.8,
            disk_usage_percent=42.1,
            disk_read_mb_s=1.25,
            disk_write_mb_s=3.40,
            net_recv_mb_s=0.55,
            net_sent_mb_s=1.10,
            raw_payload='{"test": true}',
        )
        session.add(record)
        session.commit()

        retrieved = session.query(SystemMetricModel).filter_by(hostname="web-node-01").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.instance_id, "i-0abc1234def567890")
        self.assertEqual(retrieved.cpu_percent, 45.5)
        session.close()

    def test_create_vps_scaling_alert_record(self):
        session = self.Session()
        now = datetime.now(timezone.utc)
        top_procs = [
            {"pid": 101, "name": "java", "cpu_percent": 88.5, "memory_percent": 35.0},
            {"pid": 202, "name": "python", "cpu_percent": 12.0, "memory_percent": 10.0},
        ]
        alert = VPSUsageAlertModel(
            timestamp=now,
            hostname="api-worker-03",
            instance_id="i-09988776655443322",
            instance_type="t3.large",
            availability_zone="us-east-1b",
            alert_type="HIGH_CPU",
            severity="CRITICAL",
            message="CPU utilization at 95.2% exceeds threshold 85.0%",
            cpu_percent=95.2,
            memory_percent=78.4,
            swap_percent=5.1,
            load_avg_1m=8.5,
            load_avg_5m=6.2,
            top_cpu_processes=json.dumps(top_procs),
            top_mem_processes=json.dumps(top_procs),
            resolved=False,
        )
        session.add(alert)
        session.commit()

        queried = session.query(VPSUsageAlertModel).filter_by(instance_id="i-09988776655443322").first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.alert_type, "HIGH_CPU")
        self.assertEqual(queried.severity, "CRITICAL")
        procs = json.loads(queried.top_cpu_processes)
        self.assertEqual(len(procs), 2)
        self.assertEqual(procs[0]["name"], "java")
        session.close()


if __name__ == "__main__":
    unittest.main()
