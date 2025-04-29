FROM python:3.11

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml poetry.lock ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main

# Copy application code
COPY notification /app/notification
COPY config/.env /app/notification/config/.env

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV C_FORCE_ROOT=1 

# Create startup script
RUN echo '#!/bin/bash\n\
celery -A notification.celery_app worker --loglevel=info &\n\
celery -A notification.celery_app beat --loglevel=info\n\
' > /app/start.sh && chmod +x /app/start.sh

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD celery -A notification.celery_app inspect ping -d celery@$HOSTNAME

# Run both Celery worker and beat scheduler
CMD ["/app/start.sh"]
