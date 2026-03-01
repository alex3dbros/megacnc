@echo off
title MegaCNC Manager
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0megacnc-manager.ps1"
if errorlevel 1 pause
