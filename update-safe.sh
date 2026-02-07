#!/bin/bash

# Safe update script with database backup
# This script updates the application while preserving all database data

set -e  # Exit on error

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Safe Update Script ===${NC}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}Step 1: Creating database backup...${NC}"

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}Containers not running. Starting containers first...${NC}"
    docker-compose up -d db
    sleep 5
fi

# Create database backup
if docker-compose exec -T db pg_dump -U postgres mcccnc > "$BACKUP_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓ Database backup created: ${BACKUP_FILE}${NC}"
    # Compress backup
    gzip "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup compressed: ${BACKUP_FILE}.gz${NC}"
else
    echo -e "${RED}✗ Failed to create database backup!${NC}"
    echo -e "${YELLOW}Continuing anyway...${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Stopping containers...${NC}"
docker-compose down

echo ""
echo -e "${YELLOW}Step 3: Pulling latest changes...${NC}"
git fetch --all
git pull origin main || git pull origin master

echo ""
echo -e "${YELLOW}Step 4: Rebuilding containers...${NC}"
docker-compose build

echo ""
echo -e "${YELLOW}Step 5: Starting containers...${NC}"
docker-compose up -d

echo ""
echo -e "${YELLOW}Step 6: Waiting for database to be ready...${NC}"
sleep 10

echo ""
echo -e "${YELLOW}Step 7: Running migrations...${NC}"

# Run migrations
if docker-compose exec -T web python manage.py migrate --noinput; then
    echo -e "${GREEN}✓ Migrations completed successfully${NC}"
else
    echo -e "${RED}✗ Migration failed!${NC}"
    echo -e "${YELLOW}You can restore the backup with:${NC}"
    echo "  docker-compose exec -T db psql -U postgres mcccnc < ${BACKUP_FILE}.gz | gunzip"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 8: Collecting static files...${NC}"
docker-compose exec -T web python manage.py collectstatic --noinput || true

echo ""
echo -e "${GREEN}=== Update completed successfully! ===${NC}"
echo -e "${GREEN}Backup saved at: ${BACKUP_FILE}.gz${NC}"
echo ""
echo -e "${YELLOW}To restore backup if needed:${NC}"
echo "  gunzip -c ${BACKUP_FILE}.gz | docker-compose exec -T db psql -U postgres mcccnc"
echo ""
echo -e "${YELLOW}Current directory: $(pwd)${NC}"
