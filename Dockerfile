# ==============================================================================
# Climate-Resilient Workforce Agent - Backend API Container
# ==============================================================================
FROM python:3.11-slim AS runtime

# Set environment flags for predictable Python execution in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# Install minimal OS runtime packages (curl for healthcheck)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-privileged user and group to run the application
RUN groupadd -r workforce && useradd -r -g workforce -d /app -s /sbin/nologin workforce

WORKDIR /app

# Copy project specification, source code, and offline fixtures
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY tests/fixtures/ ./tests/fixtures/

# Install the Python package with API dependencies (FastAPI + Uvicorn)
RUN pip install --no-cache-dir ".[api]" \
    && chown -R workforce:workforce /app

# Run as non-root user
USER workforce

# Expose backend port
EXPOSE 8000

# Health check to ensure the FastAPI server is responding
HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch FastAPI using Uvicorn
CMD ["uvicorn", "workforce_agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
