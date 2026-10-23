import os
import unittest
from unittest.mock import MagicMock, patch
from app.db.config import DBSettings, get_db_settings, reset_db_settings_cache


class TestDBConfig(unittest.TestCase):
    def setUp(self):
        reset_db_settings_cache()
        # Clean any existing DB env vars
        for key in ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME", "AWS_SECRET_NAME", "AWS_REGION"]:
            os.environ.pop(key, None)

    def test_unconfigured_returns_none(self):
        settings = get_db_settings()
        self.assertIsNone(settings)

    def test_load_from_environment(self):
        os.environ["DB_HOST"] = "127.0.0.1"
        os.environ["DB_PORT"] = "3306"
        os.environ["DB_USER"] = "root"
        os.environ["DB_PASSWORD"] = "secret123"
        os.environ["DB_NAME"] = "sysmon_dev"

        settings = get_db_settings()
        self.assertIsNotNone(settings)
        self.assertEqual(settings.host, "127.0.0.1")
        self.assertEqual(settings.port, 3306)
        self.assertEqual(settings.username, "root")
        self.assertEqual(settings.password, "secret123")
        self.assertEqual(settings.database, "sysmon_dev")
        self.assertEqual(settings.get_connection_url(), "mysql+pymysql://root:secret123@127.0.0.1:3306/sysmon_dev")

    @patch("app.db.config._get_boto3_secrets_client")
    def test_load_from_aws_secrets_manager(self, mock_get_client):
        os.environ["AWS_SECRET_NAME"] = "production/rds/mysql"
        os.environ["AWS_REGION"] = "us-east-1"

        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": '{"host":"rds.private.internal","port":3306,"username":"admin","password":"prodpassword","dbname":"sysmon_prod"}'
        }
        mock_get_client.return_value = mock_client

        settings = get_db_settings()
        self.assertIsNotNone(settings)
        self.assertEqual(settings.host, "rds.private.internal")
        self.assertEqual(settings.username, "admin")
        self.assertEqual(settings.password, "prodpassword")
        self.assertEqual(settings.database, "sysmon_prod")
        self.assertEqual(settings.get_connection_url(), "mysql+pymysql://admin:prodpassword@rds.private.internal:3306/sysmon_prod")


if __name__ == "__main__":
    unittest.main()
