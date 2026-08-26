@echo off
echo Starting GenshinIQ FastAPI Dev Server...
call .venv\Scripts\activate.bat
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
