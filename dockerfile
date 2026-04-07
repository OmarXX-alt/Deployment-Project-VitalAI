# Base layer
FROM python:3.11-slim AS base

WORKDIR /app

# Cache dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source application
COPY . .

# FIX: No MONGO_URI declared here to prevent accidental builds against dev (Rule 5)
ENV PORT=5000
ENV FLASK_ENV=production
ENV INIT_DB=false
EXPOSE $PORT

# Run via Gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 2 main.server.app:app"]

