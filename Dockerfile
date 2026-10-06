# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8000

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    build-essential \
    pkg-config \
    libcairo2-dev \
    netcat-openbsd \
    curl \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Create logs and media directories
RUN mkdir -p /app/ecommerce/logs /app/ecommerce/media

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Set working directory to where manage.py is
WORKDIR /app/ecommerce

# Expose default port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/ || exit 1

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Run the application using dynamic port
CMD ["/bin/sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120 --forwarded-allow-ips='*' ecommerce.wsgi:application"]

