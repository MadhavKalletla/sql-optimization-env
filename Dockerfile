# STAGE 1: Build Next.js frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# STAGE 2: Python backend
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
# Copy built Next.js output into static/ — this replaces the old static/
RUN rm -rf ./static && mkdir -p ./static
COPY --from=frontend-builder /frontend/out/ ./static/
RUN mkdir -p /tmp && chmod 777 /tmp
RUN python - <<EOF
from data.seed_database import seed_database
try:
    seed_database("data/fixtures/benchmark_seed42.db", 50000)
except Exception as e:
    print("Seeding skipped:", e)
EOF
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s \
    CMD curl -sf http://localhost:7860/health || exit 1
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]