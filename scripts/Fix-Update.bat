@echo off
title MegaCNC Update-Fix
echo.
echo MegaCNC Update-Fix
echo Datei docker-compose.yml wird zurueckgesetzt, danach startet das normale Update.
echo.

wsl --cd "/mnt/c/Users/Elitedesk/Documents/megacnc" bash -c "git checkout -- docker-compose.yml && ./update.sh"
if errorlevel 1 (
    echo.
    echo [FEHLER] Update fehlgeschlagen.
    pause
    exit /b 1
)

echo.
pause
