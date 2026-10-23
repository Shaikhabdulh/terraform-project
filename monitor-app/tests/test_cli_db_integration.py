"""Unit test for CLI database integration and graceful degradation."""

import unittest
from unittest.mock import patch, MagicMock
from app.cli import main


class TestCLIDBIntegration(unittest.TestCase):
    @patch("app.cli.Collector")
    @patch("app.cli.get_db_settings")
    @patch("app.cli.create_db_engine")
    @patch("app.cli.init_db")
    @patch("app.cli.get_session_factory")
    @patch("app.cli.persist_sample")
    def test_cli_persists_sample_when_db_configured(
        self,
        mock_persist,
        mock_get_factory,
        mock_init_db,
        mock_create_engine,
        mock_get_settings,
        mock_collector_cls,
    ):
        mock_settings = MagicMock()
        mock_settings.host = "rds-mysql.internal"
        mock_settings.port = 3306
        mock_settings.database = "sysmon_db"
        mock_get_settings.return_value = mock_settings

        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_factory = MagicMock()
        mock_get_factory.return_value = mock_factory

        collector_instance = MagicMock()
        collector_instance.sample.return_value = {
            "ts": "2026-10-23T10:00:00+0000",
            "hostname": "test-box",
            "uptime_hours": 1.0,
            "cpu": {"percent": 10.0, "cores": 2, "load_avg": [0.1, 0.1, 0.1]},
            "memory": {"percent": 20.0, "used_gb": 1.0, "total_gb": 4.0},
            "swap": {"percent": 0.0, "used_gb": 0.0},
            "disks": [],
            "disk_io": {},
            "network_io": {},
            "top_cpu": [],
            "top_mem": [],
            "alerts": [],
        }
        mock_collector_cls.return_value = collector_instance

        # Run with --once
        with patch("time.sleep", return_value=None):
            exit_code = main(["--once", "--json"])

        self.assertEqual(exit_code, 0)
        mock_get_settings.assert_called_once()
        mock_create_engine.assert_called_once_with(mock_settings)
        mock_init_db.assert_called_once_with(mock_engine)
        mock_get_factory.assert_called_once_with(mock_engine)
        mock_persist.assert_called_once()

    @patch("app.cli.Collector")
    @patch("app.cli.get_db_settings")
    @patch("app.cli.persist_sample")
    def test_cli_runs_fine_when_no_db_configured(
        self,
        mock_persist,
        mock_get_settings,
        mock_collector_cls,
    ):
        mock_get_settings.return_value = None

        collector_instance = MagicMock()
        collector_instance.sample.return_value = {
            "ts": "2026-10-23T10:00:00+0000",
            "hostname": "standalone-box",
            "uptime_hours": 1.0,
            "cpu": {"percent": 5.0, "cores": 1, "load_avg": [0.0, 0.0, 0.0]},
            "memory": {"percent": 10.0, "used_gb": 0.5, "total_gb": 2.0},
            "swap": {"percent": 0.0, "used_gb": 0.0},
            "disks": [],
            "disk_io": {},
            "network_io": {},
            "top_cpu": [],
            "top_mem": [],
            "alerts": [],
        }
        mock_collector_cls.return_value = collector_instance

        with patch("time.sleep", return_value=None):
            exit_code = main(["--once", "--json"])

        self.assertEqual(exit_code, 0)
        mock_persist.assert_not_called()


if __name__ == "__main__":
    unittest.main()
