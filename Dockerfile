﻿FROM python:3.11-slim

WORKDIR /app

# Install system packages
RUN apt-get update && apt-get install -y \
    build-essential gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

ENV PORT=8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "estatecore_backend:create_app()"]
