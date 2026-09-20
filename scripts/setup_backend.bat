@echo off
REM Sets up the CareerOS backend on Windows.
cd ..\backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
echo.
echo Installing database schema...
venv\Scripts\alembic upgrade head
echo.
echo Optional demo data: venv\Scripts\python -m app.cli seed-jobs
echo Backend setup complete. Run: uvicorn app.main:app --reload
