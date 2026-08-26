# GenshinIQ Setup Guide

## 1. Prerequisites
- **Python**: Version 3.12 or newer
- **OS**: Windows, macOS, or Linux
- **Web Browser**: Chrome, Edge, Firefox, or Safari

---

## 2. Quickstart Setup

### Step 1: Virtual Environment
Activate or initialize the virtual environment:
```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` and set your preferred UID and Gemini API Key:
```ini
APP_NAME=GenshinIQ
APP_ENV=development
DEBUG=true
HOST=127.0.0.1
PORT=8000

# User Genshin UID
USER_UID=817739968

# Gemini API Key (Required for Phase 4+)
GEMINI_API_KEY=your_gemini_api_key_here

ENKA_API_BASE_URL=https://enka.network/api
ENKA_CACHE_TTL_SECONDS=300
```

---

## 3. Running the Application

### Option A: Using Convenience Scripts
- **Start Web App**: Double click `scripts/run_server.bat` or execute `./scripts/run_server.ps1`
- **Run Automated Tests**: Double click `scripts/run_tests.bat` or execute `pytest backend/tests -v`
- **CLI Account Inspector**: Run `python scripts/import_account.py 817739968`

### Option B: Terminal Command
```powershell
.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open `http://127.0.0.1:8000/` in your browser.
