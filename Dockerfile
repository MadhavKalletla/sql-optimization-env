FROM python:3.11-slim

WORKDIR /app

# ─────────────────────────────────────────
# System dependencies
# ─────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────────
# Python dependencies
# ─────────────────────────────────────────
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────
# Copy project
# ─────────────────────────────────────────
COPY . .

RUN mkdir -p /tmp && chmod 777 /tmp

# ─────────────────────────────────────────
# Pre-seed database (FIXED ✅)
# ─────────────────────────────────────────
RUN python - <<EOF
from data.seed_database import seed_database
try:
    seed_database("data/fixtures/benchmark_seed42.db", 50000)
except Exception as e:
    print("Seeding skipped:", e)
EOF

# ─────────────────────────────────────────
# Non-root user
# ─────────────────────────────────────────
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

# ─────────────────────────────────────────
# Runtime
# ─────────────────────────────────────────
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD curl -sf http://localhost:7860/health || exit 1

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]