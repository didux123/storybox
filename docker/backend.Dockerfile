# StoryBox Backend API - Dockerfile
# Multi-stage build for optimized image size

# ===== Builder Stage =====
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-backend.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements-backend.txt

# ===== Runtime Stage =====
FROM python:3.10-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 storybox && \
    chown -R storybox:storybox /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/storybox/.local

# Copy application code
COPY app/ ./app/
COPY backend/ ./backend/
COPY configs/ ./configs/

# Set PATH to include user packages
ENV PATH=/home/storybox/.local/bin:$PATH
ENV PYTHONPATH=/app

# Switch to non-root user
USER storybox

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
