@echo off
REM Change directory to your project folder if needed
cd /d "D:\My Work\DeepCycle\Megacell Charger\megacell-cnc"

REM Activate the virtual environment
call env2\Scripts\activate.bat

REM Run Celery worker
daphne -b 0.0.0.0 -p 8080 dashboard.asgi:application
