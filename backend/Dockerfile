FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 faso && mkdir -p /app/uploads && chown faso /app/uploads
USER faso

EXPOSE 8000

# Production command (docker-compose.yml overrides it with --reload for development).
# --proxy-headers: the client IP used by rate limiting comes from X-Forwarded-For, set
# by the nginx in front (deploy/nginx). Trusting it from any address ("*") is only
# safe because this container is never published: nginx is the only way in.
# UVICORN_WORKERS: one per CPU core is a good start; rate-limit counters must then be
# shared through Redis (RATE_LIMIT_STORAGE_URI).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*' --workers ${UVICORN_WORKERS:-2}"]
