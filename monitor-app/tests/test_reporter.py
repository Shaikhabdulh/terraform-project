import io
import json
import unittest
from unittest.mock import patch
from app.reporter import format_json, print_report


class TestReporter(unittest.TestCase):
    def setUp(self):
        self.sample = {
            "ts": "2026-10-23T08:00:00+0000",
            "hostname": "test-host",
            "uptime_hours": 12.5,
            "public_ip": "1.2.3.4",
            "private_ips": {"eth0": ["10.0.0.5"]},
            "cpu": {
                "percent": 25.5,
                "per_core": [20.0, 31.0],
                "cores": 2,
                "load_avg": [0.5, 0.4, 0.3],
            },
            "memory": {
                "percent": 45.2,
                "used_gb": 3.6,
                "total_gb": 8.0,
                "available_gb": 4.4,
            },
            "swap": {"percent": 0.0, "used_gb": 0.0},
            "disks": [{"mount": "/", "total_gb": 50.0, "percent": 40.0}],
            "disk_io": {"read_mb_s": 0.1, "write_mb_s": 0.2},
            "network_io": {"recv_mb_s": 0.3, "sent_mb_s": 0.4},
            "top_cpu": [{"name": "python", "cpu_percent": 12.0}],
            "top_mem": [{"name": "python", "memory_percent": 5.0}],
        }

    def test_format_json(self):
        s_json = format_json(self.sample)
        data = json.loads(s_json)
        self.assertEqual(data["hostname"], "test-host")
        self.assertEqual(data["cpu"]["percent"], 25.5)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_print_report(self, mock_stdout):
        print_report(self.sample)
        output = mock_stdout.getvalue()
        self.assertIn("test-host", output)
        self.assertIn("25.5%", output)
        self.assertIn("1.2.3.4", output)


if __name__ == "__main__":
    unittest.main()
