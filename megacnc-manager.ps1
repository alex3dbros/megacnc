# megacnc-manager.ps1
# MegaCNC Management Script

param(
    [Parameter(Position=0)]
    [string]$Action = "menu"
)

$ProjectPath = "/mnt/c/Users/Elitedesk/Documents/megacnc"

function Show-Menu {
    Clear-Host
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "   MegaCNC Manager" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Update (pull & restart)" -ForegroundColor Yellow
    Write-Host "2. Status (show running containers)" -ForegroundColor Yellow
    Write-Host "3. Logs (show container logs)" -ForegroundColor Yellow
    Write-Host "4. Shell (open WSL in project)" -ForegroundColor Yellow
    Write-Host "5. Restart (restart all services)" -ForegroundColor Yellow
    Write-Host "6. Stop (stop all services)" -ForegroundColor Yellow
    Write-Host "7. Start (start all services)" -ForegroundColor Green
    Write-Host "Q. Quit" -ForegroundColor Yellow
    Write-Host ""
}

function Invoke-Update {
    Write-Host "[*] Updating MegaCNC..." -ForegroundColor Cyan
    wsl --cd $ProjectPath bash -c "./update.sh"
    Write-Host "[OK] Update complete!" -ForegroundColor Green
    Write-Host ""
    Pause
}

function Show-Status {
    Write-Host "[*] Container Status:" -ForegroundColor Cyan
    wsl --cd $ProjectPath bash -c "docker compose -f docker-compose.yml ps"
    Write-Host ""
    Pause
}

function Show-Logs {
    Write-Host "[*] Container Logs (Ctrl+C to exit):" -ForegroundColor Cyan
    wsl --cd $ProjectPath bash -c "docker compose -f docker-compose.yml logs -f"
}

function Open-Shell {
    Write-Host "[*] Opening WSL shell..." -ForegroundColor Cyan
    wsl --cd $ProjectPath
}

function Invoke-Restart {
    Write-Host "[*] Restarting services..." -ForegroundColor Cyan
    wsl --cd $ProjectPath bash -c "docker compose -f docker-compose.yml restart"
    Write-Host "[OK] Restart complete!" -ForegroundColor Green
    Write-Host ""
    Pause
}

function Invoke-Stop {
    Write-Host "[*] Stopping services..." -ForegroundColor Cyan
    wsl --cd $ProjectPath bash -c "docker compose -f docker-compose.yml down"
    Write-Host "[OK] Services stopped!" -ForegroundColor Green
    Write-Host ""
    Pause
}

function Invoke-Start {
    Write-Host "[*] Starting services..." -ForegroundColor Cyan
    wsl --cd $ProjectPath bash -c "docker compose -f docker-compose.yml up -d"
    Write-Host "[OK] Services started!" -ForegroundColor Green
    Write-Host ""
    Pause
}

# Handle command line arguments
switch ($Action.ToLower()) {
    "update" {
        Invoke-Update
        exit
    }
    "status" {
        Show-Status
        exit
    }
    "logs" {
        Show-Logs
        exit
    }
    "shell" {
        Open-Shell
        exit
    }
    "restart" {
        Invoke-Restart
        exit
    }
    "stop" {
        Invoke-Stop
        exit
    }
    "start" {
        Invoke-Start
        exit
    }
}

# Interactive menu
do {
    Show-Menu
    $choice = Read-Host "Select option"
    
    switch ($choice) {
        '1' { Invoke-Update }
        '2' { Show-Status }
        '3' { Show-Logs }
        '4' { Open-Shell; exit }
        '5' { Invoke-Restart }
        '6' { Invoke-Stop }
        '7' { Invoke-Start }
        'Q' { exit }
    }
} while ($choice -ne 'Q')
