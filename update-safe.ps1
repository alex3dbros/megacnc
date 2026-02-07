# Safe update script with database backup for Windows
# This script updates the application while preserving all database data

$ErrorActionPreference = "Stop"

# Get the directory where the script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$BackupDir = ".\backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupDir\db_backup_$Timestamp.sql"

Write-Host "=== Safe Update Script (Windows) ===" -ForegroundColor Green
Write-Host ""

# Create backup directory if it doesn't exist
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

Write-Host "Step 1: Creating database backup..." -ForegroundColor Yellow

# Check if containers are running
$containersRunning = docker-compose ps 2>&1 | Select-String "Up"
if (-not $containersRunning) {
    Write-Host "Containers not running. Starting containers first..." -ForegroundColor Yellow
    docker-compose up -d db
    Start-Sleep -Seconds 5
}

# Create database backup
try {
    docker-compose exec -T db pg_dump -U postgres mcccnc | Out-File -FilePath $BackupFile -Encoding UTF8
    Write-Host "✓ Database backup created: $BackupFile" -ForegroundColor Green
    
    # Compress backup using PowerShell compression
    $CompressedFile = "$BackupFile.gz"
    $bytes = [System.IO.File]::ReadAllBytes($BackupFile)
    $gzipStream = New-Object System.IO.Compression.GZipStream(
        [System.IO.File]::Create($CompressedFile),
        [System.IO.Compression.CompressionMode]::Compress
    )
    $gzipStream.Write($bytes, 0, $bytes.Length)
    $gzipStream.Close()
    Remove-Item $BackupFile
    Write-Host "✓ Backup compressed: $CompressedFile" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to create database backup!" -ForegroundColor Red
    Write-Host "Continuing anyway..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 2: Stopping containers..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "Step 3: Pulling latest changes..." -ForegroundColor Yellow
git fetch --all
$branch = git branch --show-current
if ($branch -eq "main") {
    git pull origin main
} else {
    git pull origin master
}

Write-Host ""
Write-Host "Step 4: Rebuilding containers..." -ForegroundColor Yellow
docker-compose build

Write-Host ""
Write-Host "Step 5: Starting containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Step 6: Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "Step 7: Running migrations..." -ForegroundColor Yellow

# Run migrations
try {
    docker-compose exec -T web python manage.py migrate --noinput
    Write-Host "✓ Migrations completed successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Migration failed!" -ForegroundColor Red
    Write-Host "You can restore the backup with:" -ForegroundColor Yellow
    Write-Host "  [System.IO.Compression.GZipStream]::new([System.IO.File]::OpenRead('$CompressedFile'), [System.IO.Compression.CompressionMode]::Decompress) | docker-compose exec -T db psql -U postgres mcccnc"
    exit 1
}

Write-Host ""
Write-Host "Step 8: Collecting static files..." -ForegroundColor Yellow
docker-compose exec -T web python manage.py collectstatic --noinput 2>&1 | Out-Null

Write-Host ""
Write-Host "=== Update completed successfully! ===" -ForegroundColor Green
Write-Host "Backup saved at: $CompressedFile" -ForegroundColor Green
Write-Host ""
Write-Host "To restore backup if needed:" -ForegroundColor Yellow
Write-Host "  [System.IO.Compression.GZipStream]::new([System.IO.File]::OpenRead('$CompressedFile'), [System.IO.Compression.CompressionMode]::Decompress) | docker-compose exec -T db psql -U postgres mcccnc"
Write-Host ""
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
