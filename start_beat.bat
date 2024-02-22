@echo off
REM Change directory to your project folder if needed
cd /d "D:\Projects\megacnc"

REM Activate the virtual environment
call env2\Scripts\activate.bat

REM Run Celery beat
celery -A dashboard beat --loglevel=info

REM Pause the batch script to view the output, remove or comment out this line in production
pause
