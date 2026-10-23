import unittest
from types import SimpleNamespace
from app.alerts import check_thresholds


class TestAlerts(unittest.TestCase):
    def setUp(self):
        self.default_args = SimpleNamespace(cpu=85.0, mem=85.0, disk=85.0, swap=50.0)

    def test_no_alerts_when_under_thresholds(self):
        sample = {
            "cpu": {"percent": 40.0, "cores": 4, "load_avg": [1.0, 1.0, 1.0]},
            "memory": {"percent": 60.0},
            "swap": {"percent": 10.0},
            "disks": [{"mount": "/", "percent": 50.0}],
        }
        alerts = check_thresholds(sample, self.default_args)
        self.assertEqual(alerts, [])

    def test_cpu_alert(self):
        sample = {
            "cpu": {"percent": 90.0, "cores": 4, "load_avg": [1.0, 1.0, 1.0]},
            "memory": {"percent": 60.0},
            "swap": {"percent": 10.0},
            "disks": [],
        }
        alerts = check_thresholds(sample, self.default_args)
        self.assertIn("CPU high: 90.0%", alerts)

    def test_memory_and_swap_alert(self):
        sample = {
            "cpu": {"percent": 50.0, "cores": 4, "load_avg": [1.0, 1.0, 1.0]},
            "memory": {"percent": 88.5},
            "swap": {"percent": 55.0},
            "disks": [],
        }
        alerts = check_thresholds(sample, self.default_args)
        self.assertIn("Memory high: 88.5%", alerts)
        self.assertIn("Swap in use: 55.0%", alerts)

    def test_disk_alert(self):
        sample = {
            "cpu": {"percent": 50.0, "cores": 4, "load_avg": [1.0, 1.0, 1.0]},
            "memory": {"percent": 50.0},
            "swap": {"percent": 10.0},
            "disks": [{"mount": "/data", "percent": 92.1}],
        }
        alerts = check_thresholds(sample, self.default_args)
        self.assertIn("Disk /data high: 92.1%", alerts)

    def test_load_average_alert(self):
        sample = {
            "cpu": {"percent": 50.0, "cores": 2, "load_avg": [5.5, 4.0, 3.0]},
            "memory": {"percent": 50.0},
            "swap": {"percent": 10.0},
            "disks": [],
        }
        alerts = check_thresholds(sample, self.default_args)
        self.assertIn("Load average high: 5.5", alerts)


if __name__ == "__main__":
    unittest.main()
