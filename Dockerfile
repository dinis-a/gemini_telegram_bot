FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

RUN mkdir -p /app/logs

# Run as an unprivileged user (UID can be overridden at build or run time)
ARG UID=1000
ARG GID=1000
RUN groupadd -r -g "$GID" botuser 2>/dev/null || true \
    && useradd -r -u "$UID" -g botuser botuser 2>/dev/null || true \
    && chown -R botuser:botuser /app

USER botuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*main.py" || exit 1

CMD ["python", "main.py"]
