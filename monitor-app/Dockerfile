# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS runtime

# Prevent Python from writing .pyc files and enable immediate log streaming
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create unprivileged system user and group (UID/GID 10001)
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /sbin/nologin -M appuser

# Install dependencies in a single layer with cache cleanup
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code with proper non-root ownership
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser main.py .

# Run strictly as unprivileged user
USER 10001:10001

# Graceful termination signal handling
STOPSIGNAL SIGTERM

# Default entrypoint and flags (can be overridden via compose or CLI)
ENTRYPOINT ["python", "-m", "app"]
CMD ["--json"]
