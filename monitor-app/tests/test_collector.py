import unittest
from app.collector import Collector, get_load_average


class TestCollector(unittest.TestCase):
    def test_get_load_average(self):
        load = get_load_average()
        self.assertEqual(len(load), 3)
        self.assertTrue(all(isinstance(x, (int, float)) for x in load))

    def test_collector_sample_structure(self):
        collector = Collector()
        sample = collector.sample()
        self.assertIn("ts", sample)
        self.assertIn("hostname", sample)
        self.assertIn("uptime_hours", sample)
        self.assertIn("cpu", sample)
        self.assertIn("percent", sample["cpu"])
        self.assertIn("per_core", sample["cpu"])
        self.assertIn("load_avg", sample["cpu"])
        self.assertIn("memory", sample)
        self.assertIn("swap", sample)
        self.assertIn("disks", sample)
        self.assertIn("disk_io", sample)
        self.assertIn("network_io", sample)
        self.assertIn("top_cpu", sample)
        self.assertIn("top_mem", sample)


if __name__ == "__main__":
    unittest.main()
