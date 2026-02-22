#!/bin/bash

# MegaCNC DB Restore - stellt die Datenbank aus einem Backup wieder her
# Usage: ./restore.sh backups/db_backup_20260222_120000.sql.gz

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Script-Verzeichnis ermitteln
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.yml"
BACKUP_FILE="$1"

echo ""
echo -e "${GREEN}=== MegaCNC DB Restore ===${NC}"
echo ""

# ── Prüfe Parameter ──
if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Fehler: Kein Backup-File angegeben!${NC}"
    echo ""
    echo "Usage: ./restore.sh <backup-datei>"
    echo ""
    echo "Verfuegbare Backups:"
    if [ -d "backups" ]; then
        ls -lh backups/*.sql.gz 2>/dev/null || echo "  (keine Backups gefunden)"
    else
        echo "  (kein backups/ Verzeichnis)"
    fi
    echo ""
    exit 1
fi

# ── Prüfe ob Datei existiert ──
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Fehler: Datei '$BACKUP_FILE' nicht gefunden!${NC}"
    exit 1
fi

echo -e "Backup-Datei: ${YELLOW}$BACKUP_FILE${NC}"
echo ""

# ── Step 1: Sicherheits-Backup der aktuellen DB ──
echo -e "${YELLOW}Step 1: Sicherheits-Backup der aktuellen DB...${NC}"
SAFETY_BACKUP="backups/db_before_restore_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p backups

if docker compose -f "$COMPOSE_FILE" ps 2>/dev/null | grep -q "running"; then
    if docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U postgres mcccnc > "$SAFETY_BACKUP" 2>/dev/null; then
        gzip "$SAFETY_BACKUP"
        echo -e "${GREEN}✓ Sicherheits-Backup erstellt: ${SAFETY_BACKUP}.gz${NC}"
    else
        echo -e "${YELLOW}⚠ Sicherheits-Backup fehlgeschlagen${NC}"
    fi
fi

# ── Step 2: DB Container sicherstellen ──
echo ""
echo -e "${YELLOW}Step 2: DB Container starten...${NC}"
docker compose -f "$COMPOSE_FILE" up -d db
sleep 5
echo -e "${GREEN}✓ DB Container laeuft${NC}"

# ── Step 3: Restore ──
echo ""
echo -e "${YELLOW}Step 3: Datenbank wiederherstellen...${NC}"

# DB leeren und neu erstellen
docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS mcccnc;" 2>/dev/null || true
docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -c "CREATE DATABASE mcccnc;" 2>/dev/null

# Backup einspielen (gz oder plain)
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres mcccnc
else
    docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres mcccnc < "$BACKUP_FILE"
fi

echo -e "${GREEN}✓ Datenbank wiederhergestellt${NC}"

# ── Step 4: Alle Container starten ──
echo ""
echo -e "${YELLOW}Step 4: Alle Container starten...${NC}"
docker compose -f "$COMPOSE_FILE" up -d
echo -e "${GREEN}✓ Container gestartet${NC}"

# ── Fertig ──
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Restore erfolgreich abgeschlossen!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "  Anwendung: ${GREEN}http://localhost:8000${NC}"
if [ -f "${SAFETY_BACKUP}.gz" ]; then
    echo -e "  Vorheriger Stand: ${YELLOW}${SAFETY_BACKUP}.gz${NC}"
fi
echo ""
