FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
# Ensure psycopg2 (or psycopg2-binary) is in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables
ENV FLASK_APP=wsgi.py
ENV PYTHONPATH=/app

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000
CMD ["./entrypoint.sh"]
