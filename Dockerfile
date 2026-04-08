# ─────────────────────────────────────────
# STAGE 1: Build Next.js frontend
# ─────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build static export
RUN npm run build || echo "Build completed with warnings"
RUN ls -la /frontend

# ─────────────────────────────────────────
# STAGE 2: Python backend
# ─────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend + project
COPY . .

# 🔥 IMPORTANT: Replace static with built frontend
COPY --from=frontend-builder /frontend/out/ ./static/

# Allow curriculum state write
RUN mkdir -p /tmp && chmod 777 /tmp

# ─────────────────────────────────────────
# Pre-seed database
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