# Multi-stage build: frontend → backend + static serve

# ── Stage 1: Build frontend ──
FROM node:24-slim AS builder-frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Production runtime ──
FROM python:3.12-slim
WORKDIR /app

# Dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code
COPY backend/ ./backend/

# Frontend static build → served by FastAPI
COPY --from=builder-frontend /app/frontend/dist ./static

ENV PYTHONPATH=/app
ENV STATIC_DIR=/app/static

EXPOSE 8000

# Railway sets PORT env var; fallback to 8000
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
