"""Database configuration and credential loader (AWS Secrets Manager & .env)."""
from dataclasses import dataclass
import json
import logging
import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

log = logging.getLogger("sysmon.db")

_cached_settings: Optional["DBSettings"] = None
_cache_initialized: bool = False


@dataclass
class DBSettings:
    """Database connection parameters."""
    host: str
    database: str
    username: str
    password: str
    port: int = 3306
    ssl_ca: Optional[str] = None

    def get_connection_url(self) -> str:
        """Construct standard SQLAlchemy connection URI for PyMySQL."""
        url = f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        if self.ssl_ca:
            url += f"?ssl_ca={self.ssl_ca}"
        return url


def reset_db_settings_cache():
    """Reset cached database settings (for testing or reconfiguration)."""
    global _cached_settings, _cache_initialized
    _cached_settings = None
    _cache_initialized = False


def _get_boto3_secrets_client(region_name: Optional[str] = None):
    """Factory helper to obtain a boto3 Secrets Manager client using instance role."""
    import boto3
    return boto3.client("secretsmanager", region_name=region_name)


def _load_from_aws_secrets_manager(secret_name: str, region_name: Optional[str] = None) -> Optional[DBSettings]:
    """Retrieve database credentials JSON payload from AWS Secrets Manager."""
    try:
        client = _get_boto3_secrets_client(region_name=region_name)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString")
        if not secret_string:
            log.warning("AWS Secret '%s' contains no SecretString payload", secret_name)
            return None

        data = json.loads(secret_string)
        host = data.get("host") or data.get("endpoint")
        db_name = data.get("dbname") or data.get("database") or data.get("db_name")
        username = data.get("username") or data.get("user")
        password = data.get("password") or data.get("pass")
        port = int(data.get("port", 3306))

        if not (host and db_name and username and password):
            log.warning("Secret '%s' missing required fields (host, dbname, username, password)", secret_name)
            return None

        return DBSettings(
            host=host,
            database=db_name,
            username=username,
            password=password,
            port=port,
        )
    except Exception as exc:
        log.warning("Failed to fetch database secret '%s' from AWS Secrets Manager: %s", secret_name, exc)
        return None


def get_db_settings() -> Optional[DBSettings]:
    """Resolve database settings using AWS Secrets Manager or local .env fallback."""
    global _cached_settings, _cache_initialized
    if _cache_initialized:
        return _cached_settings

    secret_name = os.environ.get("AWS_SECRET_NAME") or os.environ.get("DB_SECRET_NAME")
    region_name = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")

    settings: Optional[DBSettings] = None

    if secret_name:
        settings = _load_from_aws_secrets_manager(secret_name, region_name=region_name)

    if not settings:
        host = os.environ.get("DB_HOST")
        database = os.environ.get("DB_NAME")
        if host and database:
            username = os.environ.get("DB_USER", "root")
            password = os.environ.get("DB_PASSWORD", "")
            port = int(os.environ.get("DB_PORT", 3306))
            ssl_ca = os.environ.get("DB_SSL_CA")
            settings = DBSettings(
                host=host,
                database=database,
                username=username,
                password=password,
                port=port,
                ssl_ca=ssl_ca,
            )

    _cached_settings = settings
    _cache_initialized = True
    return _cached_settings
