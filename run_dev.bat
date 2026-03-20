@echo off
title MegaCNC Dev Server
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Applying migrations...
python manage.py migrate

echo.
echo =============================================
echo   MegaCNC dev server starting on port 8000
echo   Open http://127.0.0.1:8000 in your browser
echo   Press Ctrl+C to stop
echo =============================================
echo.
python manage.py runserver
