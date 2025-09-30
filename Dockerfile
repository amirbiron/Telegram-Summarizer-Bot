# ============================================
# Telegram Summarizer Bot - Docker Image
# ============================================
# Based on: python:3.12-slim-bookworm
# Date: 2025-09-30
# ============================================

# Stage 1: Base image with Python 3.12
FROM python:3.12-slim-bookworm as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for some Python packages
    gcc \
    # Timezone data
    tzdata \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to UTC
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


# ============================================
# Stage 2: Dependencies
# ============================================
FROM base as dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


# ============================================
# Stage 3: Final image
# ============================================
FROM dependencies as final

# Create non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# Copy application code
COPY --chown=botuser:botuser . .

# Switch to non-root user
USER botuser

# Health check (optional - checks if bot is responsive)
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Expose port (for webhooks if needed in future)
EXPOSE 8080

# Labels for metadata
LABEL maintainer="your-email@example.com"
LABEL description="Telegram Bot for Group Chat Summarization"
LABEL version="1.0.0"

# Run the bot
CMD ["python", "main.py"]
