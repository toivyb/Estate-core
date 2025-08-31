FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Put your code under a proper package name so imports work
COPY . /app/estatecore_backend
ENV PYTHONPATH=/app

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "estatecore_backend.wsgi:app"]
