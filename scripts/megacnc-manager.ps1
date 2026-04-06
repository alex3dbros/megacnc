# megacnc-manager.ps1 — MegaCNC Manager (z. B. auf Desktop kopieren)
# Zeile 10: Windows-Pfad zum Ordner "megacnc" eintragen (Repo-Root, nicht der scripts-Ordner).

param(
    [Parameter(Position = 0)]
    [string]$Action = "menu"
)

# <<< EINMAL ANPASSEN: voller Windows-Pfad zum MegaCNC-Projektordner >>>
$MegaCncRoot = "C:\Users\Elitedesk\Documents\megacnc"

function ConvertTo-WslPath {
    param([string]$WindowsPath)
    $p = $WindowsPath -replace '\\', '/'
    if ($p -match '^([A-Za-z]):(/.*)$') {
        return "/mnt/$($matches[1].ToLower())$($matches[2])"
    }
    return $WindowsPath
}

if (-not (Test-Path -LiteralPath $MegaCncRoot)) {
    Write-Host "[FEHLER] Ordner nicht gefunden: $MegaCncRoot" -ForegroundColor Red
    Write-Host "         Pfad in Zeile 10 anpassen." -ForegroundColor Yellow
    exit 1
}

$ProjectPath = ConvertTo-WslPath $MegaCncRoot
$Dc = "docker compose -f docker-compose.yml"

function Show-Menu {
    Clear-Host
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "   MegaCNC Manager" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Update (pull & restart)" -ForegroundColor Yellow
    Write-Host "2. Status" -ForegroundColor Yellow
    Write-Host "3. Logs" -ForegroundColor Yellow
    Write-Host "4. Shell (WSL im Projekt)" -ForegroundColor Yellow
    Write-Host "5. Restart" -ForegroundColor Yellow
    Write-Host "6. Stop" -ForegroundColor Yellow
    Write-Host "7. Start" -ForegroundColor Green
    Write-Host "8. Repair (nur git pull)" -ForegroundColor Magenta
    Write-Host "Q. Quit" -ForegroundColor Yellow
    Write-Host ""
}

function OkOrErr {
    param([int]$Code)
    if ($Code -ne 0) { Write-Host "[FEHLER] Exit $Code" -ForegroundColor Red; return $false }
    return $true
}

function Invoke-Update {
    Write-Host "[*] Update..." -ForegroundColor Cyan
    wsl --cd "$ProjectPath" bash -c "./update.sh"
    if (OkOrErr $LASTEXITCODE) { Write-Host "[OK] Fertig." -ForegroundColor Green }
    Pause
}

function Show-Status {
    Write-Host "[*] Status..." -ForegroundColor Cyan
    wsl --cd "$ProjectPath" bash -c "$Dc ps"
    OkOrErr $LASTEXITCODE | Out-Null
    Pause
}

function Show-Logs {
    Write-Host "[*] Logs (Strg+C Ende)..." -ForegroundColor Cyan
    wsl --cd "$ProjectPath" bash -c "$Dc logs -f"
}

function Open-Shell {
    wsl --cd "$ProjectPath"
}

function Invoke-Restart {
    Write-Host "[*] Restart..." -ForegroundColor Cyan
    wsl --cd "$ProjectPath" bash -c "$Dc restart"
    if (OkOrErr $LASTEXITCODE) { Write-Host "[OK] Fertig." -ForegroundColor Green }
    Pause
}

function Invoke-Stop {
    Write-Host "[*] Stop..." -ForegroundColor Cyan
    wsl --cd "$ProjectPath" bash -c "$Dc down"
    if (OkOrErr $LASTEXITCODE) { Write-Host "[OK] Fertig." -ForegroundColor Green }
    Pause
}

function Invoke-Start {
    Write-Host "[*] Start..." -ForegroundColor Cyan
    wsl --cd "$ProjectPath" bash -c "$Dc up -d"
    if (OkOrErr $LASTEXITCODE) { Write-Host "[OK] Fertig." -ForegroundColor Green }
    Pause
}

function Invoke-Repair {
    Write-Host "[*] Repair = git pull..." -ForegroundColor Cyan
    wsl --cd "$ProjectPath" bash -c "git pull"
    if (OkOrErr $LASTEXITCODE) {
        Write-Host "[OK] Jetzt Menue 1 (Update) ausfuehren." -ForegroundColor Green
    }
    Pause
}

switch ($Action.ToLower()) {
    "update" { Invoke-Update; exit }
    "status" { Show-Status; exit }
    "logs" { Show-Logs; exit }
    "shell" { Open-Shell; exit }
    "restart" { Invoke-Restart; exit }
    "stop" { Invoke-Stop; exit }
    "start" { Invoke-Start; exit }
    "repair" { Invoke-Repair; exit }
}

do {
    Show-Menu
    $c = Read-Host "Auswahl"
    switch ($c) {
        '1' { Invoke-Update }
        '2' { Show-Status }
        '3' { Show-Logs }
        '4' { Open-Shell; exit }
        '5' { Invoke-Restart }
        '6' { Invoke-Stop }
        '7' { Invoke-Start }
        '8' { Invoke-Repair }
        'Q' { exit }
    }
} while ($c -ne 'Q')
