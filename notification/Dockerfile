FROM python:3.11-slim

WORKDIR /app/notification

COPY notification /app/notification
COPY config/.env /app/notification/.env

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

CMD ["bash", "-c", "celery -A notification.tasks worker --beat --loglevel=info"]
