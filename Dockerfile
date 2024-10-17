# Dockerfile
FROM python:3.9-slim-bullseye

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev libffi-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc python3-dev libffi-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY src/ .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=DEBUG \
    REDIS_HOST=redis-service \
    REDIS_PORT=6379

EXPOSE 5000

CMD ["python3", "./app.py"]