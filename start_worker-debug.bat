@echo off
REM Change directory to your project folder if needed
cd /d "D:\My Work\DeepCycle\Megacell Charger\megacell-cnc"

REM Activate the virtual environment
call env2\Scripts\activate.bat

REM Run Celery worker
celery --app=dashboard worker --loglevel=debug -E --concurrency=1 --prefetch-multiplier=1

