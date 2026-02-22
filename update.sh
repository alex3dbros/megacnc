#!/bin/bash

# Navigate to your project directory
cd /home/mccadmin/megacnc

# Stop the current Docker containers
sudo docker-compose down

# Pull the latest changes, force overwrite local changes
git fetch --all
git reset --hard origin/main

# Build and start the containers
sudo docker-compose up --build -d

# Perform Django migrations
sudo docker exec megacnc-web-1 python manage.py makemigrations
sudo docker exec megacnc-web-1 python manage.py migrate
