FROM python:3.12-slim

LABEL org.opencontainers.image.title="IPGeo"
LABEL org.opencontainers.image.description="Fast, affordable IP geolocation API"
LABEL org.opencontainers.image.version="0.1.0"

# System dependencies for maxminddb
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmaxminddb0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd --create-home --shell /bin/bash ipgeo
RUN mkdir -p /app/data && chown -R ipgeo:ipgeo /app
USER ipgeo

EXPOSE 8000

ENV IPGEO_HOST=0.0.0.0
ENV IPGEO_PORT=8000
ENV IPGEO_WORKERS=4

CMD ["sh", "-c", "uvicorn app.main:app --host ${IPGEO_HOST} --port ${IPGEO_PORT} --workers ${IPGEO_WORKERS} --proxy-headers --log-level info"]
