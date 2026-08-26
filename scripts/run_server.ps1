# PowerShell script to start GenshinIQ dev server
Write-Host "Starting GenshinIQ Dev Server at http://127.0.0.1:8000/ ..." -ForegroundColor Cyan
& .venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
