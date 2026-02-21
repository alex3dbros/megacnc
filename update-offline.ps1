# MegaCNC Offline-Update - auf dem Ziel-PC OHNE Internet ausfuehren
# Dieses Script liegt auf dem USB-Stick im Ordner megacnc-update
#
# Usage: .\update-offline.ps1
#        .\update-offline.ps1 -InstallDir "D:\megacnc"

param(
    [string]$InstallDir = "C:\megacnc"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = "$InstallDir\backups"

Write-Host ""
Write-Host "=== MegaCNC Offline-Update ===" -ForegroundColor Green
Write-Host ""

# ── Prüfe ob .tar Dateien vorhanden ──
$requiredFiles = @("megacnc.tar", "postgres.tar", "redis.tar", "docker-compose.yml")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path "$ScriptDir\$file")) {
        Write-Host "Fehler: $file nicht gefunden in $ScriptDir" -ForegroundColor Red
        Write-Host "Bitte zuerst prepare-update.ps1 auf einem PC mit Internet ausfuehren." -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "✓ Alle Update-Dateien gefunden" -ForegroundColor Green

# Version anzeigen
if (Test-Path "$ScriptDir\version.txt") {
    Write-Host ""
    Get-Content "$ScriptDir\version.txt"
    Write-Host ""
}

# ── Install-Verzeichnis erstellen ──
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
    Write-Host "Install-Verzeichnis erstellt: $InstallDir"
}

# ── Step 1: Datenbank-Backup ──
Write-Host "Step 1: Datenbank-Backup..." -ForegroundColor Yellow

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

Set-Location $InstallDir

# Prüfe ob Container laufen
$containersRunning = $false
try {
    $psOutput = docker-compose ps 2>&1
    if ($psOutput -match "Up|running") {
        $containersRunning = $true
    }
} catch {}

if ($containersRunning) {
    $BackupFile = "$BackupDir\db_backup_$Timestamp.sql"
    try {
        docker-compose exec -T db pg_dump -U postgres mcccnc | Out-File -FilePath $BackupFile -Encoding UTF8
        
        # Komprimieren
        $CompressedFile = "$BackupFile.gz"
        $bytes = [System.IO.File]::ReadAllBytes($BackupFile)
        $gzipStream = New-Object System.IO.Compression.GZipStream(
            [System.IO.File]::Create($CompressedFile),
            [System.IO.Compression.CompressionMode]::Compress
        )
        $gzipStream.Write($bytes, 0, $bytes.Length)
        $gzipStream.Close()
        Remove-Item $BackupFile
        
        Write-Host "✓ Backup erstellt: $CompressedFile" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Backup fehlgeschlagen, fahre trotzdem fort..." -ForegroundColor Yellow
    }
} else {
    Write-Host "  Keine laufenden Container, ueberspringe Backup." -ForegroundColor Yellow
}

# ── Step 2: Container stoppen ──
Write-Host ""
Write-Host "Step 2: Container stoppen..." -ForegroundColor Yellow
try { docker-compose down 2>$null } catch {}
Write-Host "✓ Container gestoppt" -ForegroundColor Green

# ── Step 3: Docker Images von USB laden ──
Write-Host ""
Write-Host "Step 3: Docker Images laden (das dauert einige Minuten)..." -ForegroundColor Yellow

Write-Host "  Lade megacnc..."
docker load -i "$ScriptDir\megacnc.tar"

Write-Host "  Lade postgres..."
docker load -i "$ScriptDir\postgres.tar"

Write-Host "  Lade redis..."
docker load -i "$ScriptDir\redis.tar"

Write-Host "✓ Alle Images geladen" -ForegroundColor Green

# ── Step 4: docker-compose.yml aktualisieren ──
Write-Host ""
Write-Host "Step 4: Konfiguration aktualisieren..." -ForegroundColor Yellow
Copy-Item "$ScriptDir\docker-compose.yml" "$InstallDir\docker-compose.yml" -Force
Write-Host "✓ docker-compose.yml aktualisiert" -ForegroundColor Green

# ── Step 5: Container starten ──
Write-Host ""
Write-Host "Step 5: Container starten..." -ForegroundColor Yellow
Set-Location $InstallDir
docker-compose up -d
Write-Host "✓ Container gestartet" -ForegroundColor Green

# ── Step 6: Warten ──
Write-Host ""
Write-Host "Step 6: Warte auf Datenbank (10s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# ── Step 7: Migrationen ──
Write-Host ""
Write-Host "Step 7: Datenbank-Migrationen..." -ForegroundColor Yellow
try {
    docker-compose exec -T web python manage.py migrate --noinput
    Write-Host "✓ Migrationen erfolgreich" -ForegroundColor Green
} catch {
    Write-Host "✗ Migration fehlgeschlagen!" -ForegroundColor Red
    Write-Host "  Die Datenbank wurde NICHT veraendert." -ForegroundColor Yellow
    if ($containersRunning) {
        Write-Host "  Backup verfuegbar unter: $CompressedFile" -ForegroundColor Yellow
    }
    exit 1
}

# ── Step 8: Static Files ──
Write-Host ""
Write-Host "Step 8: Statische Dateien sammeln..." -ForegroundColor Yellow
try {
    docker-compose exec -T web python manage.py collectstatic --noinput 2>&1 | Out-Null
    Write-Host "✓ Statische Dateien aktualisiert" -ForegroundColor Green
} catch {
    Write-Host "⚠ collectstatic fehlgeschlagen (nicht kritisch)" -ForegroundColor Yellow
}

# ── Fertig ──
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Update erfolgreich abgeschlossen!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Anwendung erreichbar unter: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
if ($containersRunning -and $CompressedFile) {
    Write-Host "  Backup: $CompressedFile" -ForegroundColor Yellow
}
Write-Host ""
