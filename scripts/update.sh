#!/bin/bash

# MegaCNC Update Script - im WSL auf dem Kundensystem ausfuehren
# Usage: ./scripts/update.sh

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Repo-Root (Skript liegt in scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo -e "${GREEN}=== MegaCNC Update ===${NC}"
echo ""

# Prüfe ob docker-compose File existiert
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Fehler: $COMPOSE_FILE nicht gefunden!${NC}"
    exit 1
fi

# ── Step 1: DB Backup ──
echo -e "${YELLOW}Step 1: Datenbank-Backup...${NC}"
read -p "DB-Backup erstellen? (J/n): " DO_BACKUP
if [[ ! "$DO_BACKUP" =~ ^[nN]$ ]]; then
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"

    # DB Container starten falls nicht laufend
    docker compose -f "$COMPOSE_FILE" up -d db 2>/dev/null
    sleep 5

    if docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U postgres mcccnc > "$BACKUP_FILE" 2>/dev/null; then
        gzip "$BACKUP_FILE"
        echo -e "${GREEN}✓ Backup erstellt: ${BACKUP_FILE}.gz${NC}"
    else
        echo -e "${YELLOW}⚠ Backup fehlgeschlagen, fahre trotzdem fort...${NC}"
    fi
else
    echo -e "${YELLOW}  Backup uebersprungen.${NC}"
fi

# ── Step 2: Container stoppen ──
echo ""
echo -e "${YELLOW}Step 2: Container stoppen...${NC}"
docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
echo -e "${GREEN}✓ Container gestoppt${NC}"

# ── Step 3: Git Pull ──
echo ""
echo -e "${YELLOW}Step 3: Neueste Scripts/Config holen (git pull)...${NC}"
git pull origin main
echo -e "${GREEN}✓ Repository aktualisiert${NC}"

# ── Step 3b: Produktions-Compose-File aktivieren ──
if [ -f "deployment/docker-compose-win.yml" ]; then
    cp deployment/docker-compose-win.yml docker-compose.yml
    echo -e "${GREEN}✓ docker-compose.yml aktualisiert (Produktion)${NC}"
fi

# ── Step 4: Docker Images Pull ──
echo ""
echo -e "${YELLOW}Step 4: Neueste Docker Images herunterladen...${NC}"
docker compose -f "$COMPOSE_FILE" pull
echo -e "${GREEN}✓ Images aktualisiert${NC}"

# ── Step 5: Container starten ──
echo ""
echo -e "${YELLOW}Step 5: Container starten...${NC}"
docker compose -f "$COMPOSE_FILE" up -d
echo -e "${GREEN}✓ Container gestartet${NC}"

# ── Step 6: Warten ──
echo ""
echo -e "${YELLOW}Step 6: Warte auf Datenbank (10s)...${NC}"
sleep 10

# ── Step 7: Migrationen ──
echo ""
echo -e "${YELLOW}Step 7: Datenbank-Migrationen...${NC}"
if docker compose -f "$COMPOSE_FILE" exec -T web python manage.py migrate --noinput; then
    echo -e "${GREEN}✓ Migrationen erfolgreich${NC}"
else
    echo -e "${RED}✗ Migration fehlgeschlagen!${NC}"
    echo -e "${YELLOW}  Restore moeglich mit: ./restore.sh ${BACKUP_FILE}.gz${NC}"
    exit 1
fi

# ── Step 8: Static Files ──
echo ""
echo -e "${YELLOW}Step 8: Statische Dateien sammeln...${NC}"
docker compose -f "$COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput 2>/dev/null || true
echo -e "${GREEN}✓ Statische Dateien aktualisiert${NC}"

# ── Fertig ──
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Update erfolgreich abgeschlossen!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "  Anwendung: ${GREEN}http://localhost:8000${NC}"
if [ -f "${BACKUP_FILE}.gz" ]; then
    echo -e "  Backup:    ${YELLOW}${BACKUP_FILE}.gz${NC}"
fi
echo ""
