@echo off
REM Change directory to your project folder if needed
cd /d "D:\Projects\megacnc"

REM Activate the virtual environment
call env2\Scripts\activate.bat

REM Run Celery worker
celery -A dashboard worker --loglevel=info -E --concurrency=1 --prefetch-multiplier=1 -P solo -n w2

