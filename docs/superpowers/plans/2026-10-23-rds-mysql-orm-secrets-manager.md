# RDS MySQL ORM & AWS Secrets Manager Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate SQLAlchemy ORM into `monitor-app` to persist system metrics into Amazon RDS MySQL, supporting both local `.env` configuration and production secret retrieval via AWS Secrets Manager, with dedicated tables for high VPS usage alerts and auto-scaling telemetry.

**Architecture:** A dual-strategy database configuration engine that dynamically retrieves database credentials from AWS Secrets Manager using the EC2 instance's IAM role in production, while falling back seamlessly to local `.env` file / environment variables for local Docker development. Metric samples and scaling alert events are persisted via SQLAlchemy 2.0 ORM models using PyMySQL with connection pooling and transient retry logic across two dedicated tables: `system_metrics` (regular heartbeats) and `vps_scaling_alerts` (high utilization & scaling triggers).

**Tech Stack:** Python 3.12, SQLAlchemy 2.0, PyMySQL, python-dotenv, boto3 (graceful import for AWS Secrets Manager), AWS RDS MySQL.

**Spec:** Integration of RDS MySQL in private subnets, SQLAlchemy ORM, AWS Secrets Manager, and dedicated high-usage/scaling alert event tables.

## Global Constraints

- **Zero Plaintext Passwords in Git**: Passwords and secrets must never be committed to git or baked into Docker images.
- **Graceful Fallback**: The monitoring engine must continue operating (streaming to stdout/JSON) even if the database is temporarily unreachable or unconfigured.
- **Private Subnet Reality**: In production AWS, RDS in private subnets is addressed via its VPC endpoint DNS (`*.rds.amazonaws.com`), never `localhost`.
- **IAM Instance Profile**: On EC2, AWS Secrets Manager calls must use instance IAM roles via IMDSv2 without requiring static AWS access keys.
- **Dedicated Alert Separation**: High VPS usage and scaling events are written to a separate table `vps_scaling_alerts` designed for long-term historical query performance and future web dashboards.

## Review Focus

1. **Database Unreachable / Cold Start**: Application must not crash if RDS is still initializing; samples should log a warning and continue monitoring.
2. **Secrets Manager Throttle / Cache**: Database credentials retrieved from Secrets Manager should be cached in-memory and not queried on every 10-second monitoring cycle.
3. **Connection Pool Recurrence**: Handle MySQL `server has gone away` (idle timeout in private subnets) by enabling `pool_recycle=3600` and `pool_pre_ping=True`.
4. **Local Development Fallback**: When `AWS_SECRET_NAME` is absent, automatically parse `.env` without requiring AWS credentials.
5. **Detailed Scaling Root Cause**: The alert record must snapshot top CPU and Memory processes at the exact moment of the spike so scaling events can be audited later.

---

### Task 1: Dependencies and Environment Configuration Engine

**Files:**
- Modify: `monitor-app/requirements.txt`
- Create: `monitor-app/app/db/__init__.py`
- Create: `monitor-app/app/db/config.py`
- Test: `monitor-app/tests/test_db_config.py`

**Interfaces:**
- Produces: `get_db_settings() -> Optional[DBSettings]`
- Produces: `DBSettings` dataclass (`host`, `port`, `username`, `password`, `database`, `ssl_ca`, `get_connection_url()`)

- [ ] **Step 1: Write the failing unit test for `get_db_settings()`**
  Create `monitor-app/tests/test_db_config.py` testing:
  1. Loading credentials from `.env` / environment variables (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).
  2. Mocking AWS Secrets Manager JSON payload retrieval when `AWS_SECRET_NAME` is present.
  3. Graceful `None` return when database is disabled or unconfigured.

- [ ] **Step 2: Run test to verify it fails**
  Run: `uv run python -m unittest monitor-app/tests/test_db_config.py`
  Expected: FAIL (`ModuleNotFoundError: No module named 'app.db'`)

- [ ] **Step 3: Update `requirements.txt` and implement `app/db/config.py`**
  - Add `sqlalchemy>=2.0.0`, `pymysql>=1.1.0`, `python-dotenv>=1.0.0`, `boto3>=1.34.0` to `requirements.txt`.
  - Implement `get_db_settings()`:
    - Checks for `AWS_SECRET_NAME` (or `DB_SECRET_NAME`). If present, queries AWS Secrets Manager via `boto3.client('secretsmanager')` using default credential provider chain (IAM instance role).
    - If `AWS_SECRET_NAME` is not set, loads `.env` using `python-dotenv` and reads `DB_*` variables.
    - Caches settings to prevent re-querying Secrets Manager on every call.

- [ ] **Step 4: Run test to verify it passes**
  Run: `uv run --with sqlalchemy --with pymysql --with python-dotenv --with boto3 python -m unittest monitor-app/tests/test_db_config.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add monitor-app/requirements.txt monitor-app/app/db/ monitor-app/tests/test_db_config.py
  git commit -m "feat(db): add database configuration engine with AWS Secrets Manager support"
  ```

---

### Task 2: SQLAlchemy ORM Models and Dedicated VPS Scaling Alert Schema

**Files:**
- Create: `monitor-app/app/db/models.py`
- Create: `monitor-app/app/db/session.py`
- Test: `monitor-app/tests/test_db_models.py`

**Interfaces:**
- Produces: `Base = declarative_base()`
- Produces: `SystemMetricModel` (table: `system_metrics`): Heartbeat metrics telemetry.
- Produces: `VPSUsageAlertModel` (table: `vps_scaling_alerts`): High resource utilization, scaling events, spike metrics, top consuming processes.
- Produces: `get_engine()`, `get_session_factory()`, `init_db()`

- [ ] **Step 1: Write the failing unit test for ORM models and schema initialization**
  Create `monitor-app/tests/test_db_models.py` using SQLite in-memory for testing:
  - Verify tables `system_metrics` and `vps_scaling_alerts` are created properly.
  - Verify inserting `SystemMetricModel` and `VPSUsageAlertModel` with top process JSON snapshots.

- [ ] **Step 2: Run test to verify it fails**
  Run: `uv run python -m unittest monitor-app/tests/test_db_models.py`
  Expected: FAIL with missing module `app.db.models`.

- [ ] **Step 3: Implement `app/db/models.py` and `app/db/session.py`**
  - Define `SystemMetricModel` and `VPSUsageAlertModel` declarative models in `models.py`.
  - In `session.py`, implement `create_db_engine(db_settings)` with `pool_recycle=3600`, `pool_pre_ping=True`, and `pool_size=5`.
  - Implement `init_db(engine)` to create tables automatically.

- [ ] **Step 4: Run test to verify it passes**
  Run: `uv run --with sqlalchemy --with pymysql --with python-dotenv python -m unittest monitor-app/tests/test_db_models.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add monitor-app/app/db/models.py monitor-app/app/db/session.py monitor-app/tests/test_db_models.py
  git commit -m "feat(db): define SQLAlchemy models for system metrics and vps scaling alerts"
  ```

---

### Task 3: Metric & VPS Scaling Alert Persistence Service

**Files:**
- Create: `monitor-app/app/db/repository.py`
- Test: `monitor-app/tests/test_db_repository.py`

**Interfaces:**
- Consumes: `SystemMetricModel`, `VPSUsageAlertModel`, `sessionmaker`
- Produces: `persist_sample(session_factory, sample: dict) -> bool`
- Produces: `persist_scaling_alert(session_factory, alert_data: dict) -> bool`

- [ ] **Step 1: Write the failing unit test for `persist_sample` and `persist_scaling_alert`**
  Create `monitor-app/tests/test_db_repository.py`:
  - Pass a standard sample dictionary and verify `SystemMetricModel` record is created.
  - When threshold alerts are triggered (e.g. CPU > 85% or Memory > 85%), verify corresponding `VPSUsageAlertModel` records are written with top process details.
  - Verify graceful failure handling (`OperationalError` handled without app crashing).

- [ ] **Step 2: Run test to verify it fails**
  Run: `uv run python -m unittest monitor-app/tests/test_db_repository.py`
  Expected: FAIL (`ModuleNotFoundError: No module named 'app.db.repository'`)

- [ ] **Step 3: Implement persistence logic in `app/db/repository.py`**
  - Insert normal heartbeat telemetry into `system_metrics`.
  - When alerts are detected, insert detailed diagnostic snapshot into `vps_scaling_alerts`.
  - Catch `SQLAlchemyError`, log structured error, rollback transaction, and return `False`.

- [ ] **Step 4: Run test to verify it passes**
  Run: `uv run --with sqlalchemy --with pymysql --with python-dotenv python -m unittest monitor-app/tests/test_db_repository.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add monitor-app/app/db/repository.py monitor-app/tests/test_db_repository.py
  git commit -m "feat(db): add persistence repository for metrics and scaling alerts"
  ```

---

### Task 4: Integrate Persistence into CLI Monitoring Loop

**Files:**
- Modify: `monitor-app/app/cli.py`
- Test: `monitor-app/tests/test_cli_db_integration.py`

**Interfaces:**
- Consumes: `get_db_settings()`, `create_db_engine()`, `init_db()`, `persist_sample()`
- Produces: Seamless periodic database writes without disrupting CLI output.

- [ ] **Step 1: Write failing unit test for CLI integration**
  Create `monitor-app/tests/test_cli_db_integration.py`:
  - Test running CLI `--once` with mocked DB engine.
  - Verify persistence is invoked.
  - Verify CLI operates normally when DB is unconfigured.

- [ ] **Step 2: Run test to verify it fails**
  Run: `uv run python -m unittest monitor-app/tests/test_cli_db_integration.py`
  Expected: FAIL

- [ ] **Step 3: Update `app/cli.py`**
  - Attempt database setup at startup.
  - On each sample, persist metrics and any triggered alerts.

- [ ] **Step 4: Run test to verify it passes**
  Run: `uv run --with sqlalchemy --with pymysql --with python-dotenv --with boto3 python -m unittest monitor-app/tests/test_cli_db_integration.py`
  Expected: PASS

- [ ] **Step 5: Commit**
  ```bash
  git add monitor-app/app/cli.py monitor-app/tests/test_cli_db_integration.py
  git commit -m "feat(cli): wire database persistence and alert recording into monitor loop"
  ```

---

### Task 5: Docker, Terraform & AWS Secrets Manager Guide

**Files:**
- Create: `monitor-app/.env.example`
- Modify: `monitor-app/docker-compose.yml`
- Modify: `monitor-app/Dockerfile`
- Create: `docs/aws-secrets-manager-rds.md`
- Modify: `docs/index.md`

- [ ] **Step 1: Create `monitor-app/.env.example`**
- [ ] **Step 2: Update `docker-compose.yml` to pass database environment variables**
- [ ] **Step 3: Document RDS MySQL private subnet setup, IAM policies, and table schema in `docs/aws-secrets-manager-rds.md`**
- [ ] **Step 4: Run full test suite**
- [ ] **Step 5: Commit and Sync**
