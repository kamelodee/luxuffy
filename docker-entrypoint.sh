#!/bin/bash

# Wait for database to be ready
echo "Waiting for postgres..."
python << END
import socket
import time
import os

host = os.environ.get('DB_HOST', 'db')
port = int(os.environ.get('DB_PORT', 5432))
max_attempts = 30

for attempt in range(max_attempts):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        if result == 0:
            print("PostgreSQL is ready!")
            break
        sock.close()
    except Exception as e:
        print(f"Connection attempt {attempt + 1} failed: {e}")
    
    time.sleep(2)
else:
    print("Failed to connect to PostgreSQL after {} attempts".format(max_attempts))
    exit(1)
END

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Create superuser if not exists
echo "Creating superuser..."
python manage.py createsuperuser --noinput || true

# Start server
echo "Starting server..."
exec "$@"