# MegaCNC Update vorbereiten - auf einem PC MIT Internet ausführen
# Erkennt USB-Laufwerke automatisch und speichert alle Docker-Images darauf
#
# Usage: .\prepare-update.ps1
#        .\prepare-update.ps1 -UsbPath "E:\megacnc-update"

param(
    [string]$UsbPath = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$UpdateFolder = "megacnc-update"

$IMAGE_APP   = "ghcr.io/heinz-leiser-ai/megacnc:latest"
$IMAGE_DB    = "postgres:15"
$IMAGE_REDIS = "redis:alpine"

Write-Host ""
Write-Host "=== MegaCNC Update vorbereiten ===" -ForegroundColor Green
Write-Host ""

# ── USB-Laufwerk erkennen falls nicht angegeben ──
if (-not $UsbPath) {
    Write-Host "Suche USB-Laufwerke..." -ForegroundColor Yellow
    
    # Alle Wechseldatenträger finden
    $usbDrives = Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 2 } | 
        Select-Object DeviceID, VolumeName, 
            @{Name="FreeGB"; Expression={[math]::Round($_.FreeSpace / 1GB, 1)}},
            @{Name="SizeGB"; Expression={[math]::Round($_.Size / 1GB, 1)}}

    if ($usbDrives.Count -eq 0) {
        Write-Host "Kein USB-Laufwerk gefunden!" -ForegroundColor Red
        Write-Host "Bitte USB-Stick einstecken oder Pfad manuell angeben:" -ForegroundColor Yellow
        Write-Host '  .\prepare-update.ps1 -UsbPath "E:\megacnc-update"' -ForegroundColor Yellow
        exit 1
    }

    Write-Host ""
    Write-Host "Gefundene USB-Laufwerke:" -ForegroundColor Cyan
    Write-Host "  Nr  Laufwerk  Name                Frei     Gesamt" -ForegroundColor Cyan
    Write-Host "  --  --------  ----                ----     ------" -ForegroundColor Cyan
    
    $i = 1
    foreach ($drive in $usbDrives) {
        $name = if ($drive.VolumeName) { $drive.VolumeName } else { "(kein Name)" }
        Write-Host ("  {0}   {1}         {2,-20}{3,5} GB  {4,5} GB" -f $i, $drive.DeviceID, $name, $drive.FreeGB, $drive.SizeGB)
        $i++
    }
    Write-Host ""

    if ($usbDrives.Count -eq 1) {
        $selected = $usbDrives
        Write-Host "Nur ein USB-Laufwerk gefunden: $($selected.DeviceID)" -ForegroundColor Yellow
    } else {
        $choice = Read-Host "Welches Laufwerk verwenden? (1-$($usbDrives.Count))"
        $idx = [int]$choice - 1
        if ($idx -lt 0 -or $idx -ge $usbDrives.Count) {
            Write-Host "Ungueltige Auswahl!" -ForegroundColor Red
            exit 1
        }
        $selected = $usbDrives[$idx]
    }

    # Prüfe freien Speicherplatz (min. 3 GB empfohlen)
    if ($selected.FreeGB -lt 3) {
        Write-Host "Warnung: Nur $($selected.FreeGB) GB frei. Empfohlen: mindestens 3 GB." -ForegroundColor Yellow
        $confirm = Read-Host "Trotzdem fortfahren? (j/N)"
        if ($confirm -notmatch '^[jJyY]$') { exit 0 }
    }

    $UsbPath = "$($selected.DeviceID)\$UpdateFolder"
    Write-Host ""
    Write-Host "Zielordner: $UsbPath" -ForegroundColor Green
}

# ── Zielordner erstellen ──
if (-not (Test-Path $UsbPath)) {
    New-Item -ItemType Directory -Path $UsbPath | Out-Null
}

# ── Step 1: GHCR Login & Pull ──
Write-Host ""
Write-Host "Step 1: Docker Images herunterladen..." -ForegroundColor Yellow

if ($env:GHCR_TOKEN) {
    Write-Host "  Login bei ghcr.io..."
    $env:GHCR_TOKEN | docker login ghcr.io -u "heinz-leiser-ai" --password-stdin
} else {
    Write-Host "  GHCR_TOKEN nicht gesetzt - versuche ohne Login..." -ForegroundColor Yellow
    Write-Host '  Falls noetig: $env:GHCR_TOKEN = "ghp_DEIN_TOKEN"' -ForegroundColor Yellow
}

Write-Host "  Pulling $IMAGE_APP ..."
docker pull $IMAGE_APP

Write-Host "  Pulling $IMAGE_DB ..."
docker pull $IMAGE_DB

Write-Host "  Pulling $IMAGE_REDIS ..."
docker pull $IMAGE_REDIS

Write-Host "✓ Alle Images heruntergeladen" -ForegroundColor Green

# ── Step 2: Images als .tar speichern ──
Write-Host ""
Write-Host "Step 2: Images als .tar auf USB speichern..." -ForegroundColor Yellow
Write-Host "  (Das kann einige Minuten dauern)"

Write-Host "  Speichere megacnc.tar ..."
docker save -o "$UsbPath\megacnc.tar" $IMAGE_APP

Write-Host "  Speichere postgres.tar ..."
docker save -o "$UsbPath\postgres.tar" $IMAGE_DB

Write-Host "  Speichere redis.tar ..."
docker save -o "$UsbPath\redis.tar" $IMAGE_REDIS

Write-Host "✓ Alle Images gespeichert" -ForegroundColor Green

# ── Step 3: Deployment-Dateien kopieren ──
Write-Host ""
Write-Host "Step 3: Deployment-Dateien kopieren..." -ForegroundColor Yellow

Copy-Item "$ScriptDir\deployment\docker-compose-win.yml" "$UsbPath\docker-compose.yml" -Force
Copy-Item "$ScriptDir\update-offline.ps1" "$UsbPath\update-offline.ps1" -Force

# Version-Info schreiben
$versionInfo = @"
MegaCNC Update Package
======================
Erstellt:  $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Images:    $IMAGE_APP
           $IMAGE_DB
           $IMAGE_REDIS
"@
$versionInfo | Out-File "$UsbPath\version.txt" -Encoding UTF8

Write-Host "✓ Dateien kopiert" -ForegroundColor Green

# ── Zusammenfassung ──
$totalSize = (Get-ChildItem $UsbPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Update-Paket erfolgreich erstellt!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Ordner:  $UsbPath"
Write-Host "  Groesse: $([math]::Round($totalSize)) MB"
Write-Host ""
Write-Host "  Inhalt:" -ForegroundColor Cyan
Get-ChildItem $UsbPath | ForEach-Object {
    $size = [math]::Round($_.Length / 1MB, 1)
    Write-Host ("    {0,-25} {1,8} MB" -f $_.Name, $size)
}
Write-Host ""
Write-Host "  Naechster Schritt:" -ForegroundColor Yellow
Write-Host "  1. USB-Stick zum Ziel-PC bringen"
Write-Host "  2. PowerShell als Admin oeffnen"
Write-Host ('  3. Ausfuehren: X:\' + $UpdateFolder + '\update-offline.ps1')
Write-Host ""
