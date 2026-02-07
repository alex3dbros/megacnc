# Update Guide - Daten sicher updaten

## Wichtige Hinweise

**⚠️ WICHTIG:** Vor jedem Update sollte ein Datenbank-Backup erstellt werden, um Datenverlust zu vermeiden.

## Automatisches Update mit Backup (Empfohlen)

### Linux / macOS / WSL

Das Script `update-safe.sh` führt automatisch ein Backup durch und aktualisiert die App:

```bash
# Im Projektverzeichnis ausführen
./update-safe.sh
```

### Windows (PowerShell)

Das Script `update-safe.ps1` führt automatisch ein Backup durch und aktualisiert die App:

```powershell
# Im Projektverzeichnis ausführen
.\update-safe.ps1
```

**Hinweis:** Falls PowerShell die Ausführung blockiert:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\update-safe.ps1
```

**Hinweis:** Das Script verwendet relative Pfade und funktioniert von jedem Verzeichnis aus, solange es im Projektverzeichnis ausgeführt wird.

**Was das Script macht:**
1. ✅ Erstellt automatisch ein Datenbank-Backup
2. ✅ Stoppt die Container
3. ✅ Lädt die neuesten Änderungen
4. ✅ Baut die Container neu
5. ✅ Startet die Container
6. ✅ Führt Migrationen aus
7. ✅ Sammelt statische Dateien

**Backup-Speicherort:** `backups/db_backup_YYYYMMDD_HHMMSS.sql.gz`

## Manuelles Update mit Backup

### Schritt 1: Datenbank-Backup erstellen

**Linux / macOS / WSL:**
```bash
# Container starten (falls nicht laufend)
docker-compose up -d db

# Backup erstellen
mkdir -p backups
docker-compose exec db pg_dump -U postgres mcccnc > backups/db_backup_$(date +%Y%m%d_%H%M%S).sql

# Optional: Backup komprimieren
gzip backups/db_backup_*.sql
```

**Windows (PowerShell):**
```powershell
# Container starten (falls nicht laufend)
docker-compose up -d db

# Backup erstellen
New-Item -ItemType Directory -Force -Path backups | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
docker-compose exec db pg_dump -U postgres mcccnc | Out-File -FilePath "backups\db_backup_$timestamp.sql" -Encoding UTF8

# Optional: Backup komprimieren (PowerShell)
$file = "backups\db_backup_$timestamp.sql"
$bytes = [System.IO.File]::ReadAllBytes($file)
$gzipStream = New-Object System.IO.Compression.GZipStream(
    [System.IO.File]::Create("$file.gz"),
    [System.IO.Compression.CompressionMode]::Compress
)
$gzipStream.Write($bytes, 0, $bytes.Length)
$gzipStream.Close()
Remove-Item $file
```

### Schritt 2: Code aktualisieren

```bash
# Im Projektverzeichnis (relativer Pfad)
# Änderungen holen
git fetch --all
git pull origin main  # oder master

# Container stoppen
docker-compose down
```

### Schritt 3: Container neu bauen

```bash
# Container neu bauen
docker-compose build

# Container starten
docker-compose up -d
```

### Schritt 4: Migrationen ausführen

```bash
# Warten bis Datenbank bereit ist
sleep 10

# Migrationen ausführen
docker-compose exec web python manage.py migrate

# Statische Dateien sammeln (optional)
docker-compose exec web python manage.py collectstatic --noinput
```

## Backup wiederherstellen (falls nötig)

### Linux / macOS / WSL

Falls nach dem Update Probleme auftreten:

```bash
# Container stoppen
docker-compose down

# Datenbank-Volume löschen (ACHTUNG: Alle Daten gehen verloren!)
docker volume rm megacnc_postgres_data

# Container neu starten
docker-compose up -d db

# Backup wiederherstellen
gunzip -c backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | docker-compose exec -T db psql -U postgres mcccnc

# Container neu starten
docker-compose up -d
```

### Windows (PowerShell)

Falls nach dem Update Probleme auftreten:

```powershell
# Container stoppen
docker-compose down

# Datenbank-Volume löschen (ACHTUNG: Alle Daten gehen verloren!)
docker volume rm megacnc_postgres_data

# Container neu starten
docker-compose up -d db

# Backup wiederherstellen (PowerShell)
$backupFile = "backups\db_backup_YYYYMMDD_HHMMSS.sql.gz"
$gzipStream = [System.IO.Compression.GZipStream]::new(
    [System.IO.File]::OpenRead($backupFile),
    [System.IO.Compression.CompressionMode]::Decompress
)
$gzipStream | docker-compose exec -T db psql -U postgres mcccnc
$gzipStream.Close()

# Container neu starten
docker-compose up -d
```

## Update ohne Datenverlust - Checkliste

- [ ] Datenbank-Backup erstellt
- [ ] Backup-Datei überprüft (nicht leer)
- [ ] Code aktualisiert
- [ ] Container neu gebaut
- [ ] Migrationen erfolgreich ausgeführt
- [ ] App funktioniert korrekt
- [ ] Daten sind noch vorhanden

## Häufige Probleme

### Migration-Fehler

```bash
# Migrationen zusammenführen (bei Konflikten)
docker-compose exec web python manage.py makemigrations --merge

# Dann erneut migrieren
docker-compose exec web python manage.py migrate
```

### Container-Name geändert

Falls der Container-Name nicht `megacnc_web_1` ist:

```bash
# Container-Namen finden
docker-compose ps

# Dann mit richtigem Namen arbeiten
docker exec <CONTAINER_NAME> python manage.py migrate
```

## Automatische Backups einrichten

Für regelmäßige automatische Backups (z.B. täglich):

```bash
# Crontab bearbeiten
crontab -e

# Täglich um 2 Uhr morgens Backup erstellen
# WICHTIG: Absoluten Pfad zum Projektverzeichnis angeben!
0 2 * * * cd /pfad/zum/megacnc && docker-compose exec -T db pg_dump -U postgres mcccnc | gzip > backups/db_backup_$(date +\%Y\%m\%d).sql.gz
```
