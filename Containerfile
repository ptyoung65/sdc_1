# Multi-stage Podman/Docker build for SDC application

# Stage 1: Frontend Builder
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 2: Backend Builder
FROM python:3.11-slim AS backend-builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements-minimal.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --user -r requirements-minimal.txt && \
    pip install --no-cache-dir --user google-generativeai python-dotenv

# Stage 3: Final Runtime Image
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=backend-builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy backend application
COPY --chown=appuser:appuser backend/ ./backend/

# Copy frontend build
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/out ./frontend/dist

# Copy startup scripts
COPY --chown=appuser:appuser scripts/ ./scripts/

# Make scripts executable
RUN chmod +x scripts/*.sh

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Environment variables
ENV PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose ports
EXPOSE 8000 3000

# Default command
CMD ["python", "-m", "uvicorn", "backend.api_main:app", "--host", "0.0.0.0", "--port", "8000"]