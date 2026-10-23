import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from app.identity import get_instance_info, get_private_ips, get_public_ip, imds_get, reset_imds_cache


class TestIdentity(unittest.TestCase):
    def setUp(self):
        reset_imds_cache()
    @patch("app.identity._http")
    def test_imds_get_success(self, mock_http):
        mock_http.side_effect = ["dummy-token", "i-1234567890abcdef0"]
        val = imds_get("instance-id")
        self.assertEqual(val, "i-1234567890abcdef0")

    @patch("app.identity._http")
    def test_imds_get_failure(self, mock_http):
        mock_http.side_effect = urllib.error.URLError("Connection refused")
        val = imds_get("instance-id")
        self.assertIsNone(val)

    @patch("app.identity.imds_get")
    def test_get_public_ip_from_imds(self, mock_imds):
        mock_imds.return_value = "54.210.1.2"
        ip = get_public_ip()
        self.assertEqual(ip, "54.210.1.2")

    @patch("app.identity.imds_get")
    @patch("app.identity._http")
    def test_get_public_ip_fallback(self, mock_http, mock_imds):
        mock_imds.return_value = None
        mock_http.return_value = "198.51.100.42"
        ip = get_public_ip()
        self.assertEqual(ip, "198.51.100.42")

    def test_get_private_ips(self):
        ips = get_private_ips()
        self.assertIsInstance(ips, dict)
        for iface, addrs in ips.items():
            for addr in addrs:
                self.assertFalse(addr.startswith("127."))

    @patch("app.identity.imds_get")
    def test_get_instance_info(self, mock_imds):
        mock_imds.side_effect = lambda path: f"val-{path}"
        info = get_instance_info()
        self.assertIn("instance_id", info)
        self.assertIn("instance_type", info)
        self.assertIn("availability_zone", info)
        self.assertIn("private_ip_imds", info)
        self.assertIn("mac", info)


if __name__ == "__main__":
    unittest.main()
