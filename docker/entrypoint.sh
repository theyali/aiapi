#!/bin/sh

set -e

if [ "$#" -gt 0 ]; then
    echo "Starting custom command: $@"
    exec "$@"
fi

echo "Applying migrations..."
python manage.py migrate

if [ "$DEBUG" = "True" ]; then
    echo "Starting Django runserver because DEBUG=True"
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    echo "Starting Gunicorn because DEBUG=False"
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi