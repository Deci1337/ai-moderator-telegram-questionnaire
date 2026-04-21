FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY . .

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /usr/local

COPY --from=builder /app /app

RUN find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

ENV PYTHONPATH=/app

USER appuser

EXPOSE 8003

CMD ["python", "main.py"]