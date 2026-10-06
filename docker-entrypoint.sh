#!/bin/bash
set -e

# Wait for database to be ready (supports DATABASE_URL, DB_HOST, or SQLite)
echo "Checking database connectivity..."
export DJANGO_SETTINGS_MODULE=ecommerce.settings

python << 'END'
import os
import sys
import time
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()
from django.db import connections
from django.db.utils import OperationalError

max_retries = 30
for i in range(max_retries):
    try:
        conn = connections['default']
        conn.cursor()
        print("Database connection successfully established!")
        sys.exit(0)
    except OperationalError as e:
        print(f"Waiting for database to become ready... ({i+1}/{max_retries})")
        time.sleep(1)
    except Exception as e:
        print(f"Database check notice: {e}")
        sys.exit(0)

print("Database check timeout reached, continuing...")
END

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Create default superuser if it doesn't already exist
echo "Ensuring administrative user exists..."
python << 'END'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser "{username}" created.')
else:
    print(f'Superuser "{username}" already exists.')
END

# Collect static files for WhiteNoise
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "collectstatic warning, serving via WhiteNoise finders"

# Start the application server
echo "Starting application server..."
exec "$@"
