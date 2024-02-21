#!/bin/bash

# Exit on any non-zero status.
trap 'exit' ERR
set -E

# Run Django database migrations
echo "Running makemigrations..."
python manage.py makemigrations

echo "Running migrate..."
python manage.py migrate

# Start Gunicorn (or another WSGI server) with your Django project
# Adjust the command below according to your setup
gunicorn dashboard.wsgi:application --bind 0.0.0.0:8000