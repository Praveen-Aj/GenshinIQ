@echo off
echo Running GenshinIQ Automated Test Suite...
call .venv\Scripts\activate.bat
pytest backend/tests -v
pause
