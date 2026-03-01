#!/bin/bash

# Deploy script for GitHub Container Registry (ghcr.io)
# Usage: ./deploy-ghcr.sh [version]
# Example: ./deploy-ghcr.sh v1.0.0

set -e

# Configuration
REGISTRY="ghcr.io"
OWNER="heinz-leiser-ai"
IMAGE_NAME="megacnc"
FULL_IMAGE="${REGISTRY}/${OWNER}/${IMAGE_NAME}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Version from argument or generate from date
VERSION="${1:-$(date +%Y%m%d-%H%M%S)}"

echo -e "${GREEN}=== Deploy to GitHub Container Registry ===${NC}"
echo -e "Image: ${FULL_IMAGE}"
echo -e "Version: ${VERSION}"
echo ""

# Check for GHCR_TOKEN environment variable
if [ -z "$GHCR_TOKEN" ]; then
    echo -e "${RED}Error: GHCR_TOKEN environment variable not set${NC}"
    echo ""
    echo "To set up:"
    echo "1. Create a Personal Access Token at GitHub:"
    echo "   https://github.com/settings/tokens/new"
    echo "   Required scopes: write:packages, read:packages, delete:packages"
    echo ""
    echo "2. Export the token:"
    echo "   export GHCR_TOKEN='your_token_here'"
    echo ""
    echo "3. Or add to ~/.bashrc for persistence"
    exit 1
fi

# Optional: Create DB backup before deploy
read -p "Create database backup before deploy? (y/N): " CREATE_BACKUP
if [[ "$CREATE_BACKUP" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Creating database backup...${NC}"
    mkdir -p backups
    BACKUP_FILE="backups/db_backup_predeploy_$(date +%Y%m%d_%H%M%S).sql"
    
    if docker-compose exec -T db pg_dump -U postgres mcccnc > "$BACKUP_FILE" 2>/dev/null; then
        gzip "$BACKUP_FILE"
        echo -e "${GREEN}✓ Backup created: ${BACKUP_FILE}.gz${NC}"
    else
        echo -e "${YELLOW}⚠ Could not create backup (containers not running?)${NC}"
    fi
fi

# Login to ghcr.io
echo -e "${YELLOW}Step 1: Logging in to ghcr.io...${NC}"
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$OWNER" --password-stdin
echo -e "${GREEN}✓ Login successful${NC}"

# Build image
echo ""
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
docker build -t "${FULL_IMAGE}:${VERSION}" -t "${FULL_IMAGE}:latest" .
echo -e "${GREEN}✓ Image built${NC}"

# Push images
echo ""
echo -e "${YELLOW}Step 3: Pushing images to ghcr.io...${NC}"
docker push "${FULL_IMAGE}:${VERSION}"
docker push "${FULL_IMAGE}:latest"
echo -e "${GREEN}✓ Images pushed${NC}"

# Cleanup: alte Images aufräumen, nur letzte 2 Versionen behalten
echo ""
echo -e "${YELLOW}Step 4: Alte Images aufräumen...${NC}"

OLD_IMAGES=$(docker images "${FULL_IMAGE}" --format "{{.ID}} {{.Tag}}" | grep -v "latest" | tail -n +3 | awk '{print $1}')
if [ -n "$OLD_IMAGES" ]; then
    echo "$OLD_IMAGES" | xargs docker rmi -f 2>/dev/null || true
    echo -e "${GREEN}✓ Alte Images entfernt${NC}"
else
    echo -e "${GREEN}✓ Keine alten Images zum Aufräumen${NC}"
fi

# Dangling Images und Build-Cache entfernen
docker image prune -f 2>/dev/null || true
docker builder prune -f 2>/dev/null || true
echo -e "${GREEN}✓ Build-Cache aufgeräumt${NC}"

# Summary
echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Images available at:"
echo "  ${FULL_IMAGE}:${VERSION}"
echo "  ${FULL_IMAGE}:latest"
echo ""
echo "To pull on production server:"
echo "  docker pull ${FULL_IMAGE}:latest"
