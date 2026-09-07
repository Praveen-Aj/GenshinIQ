# GenshinIQ Setup & Developer Guide

## 1. Prerequisites
- **Python**: Version 3.12 or newer (recommended 3.12.x)
- **Git**: Installed and accessible in terminal
- **Operating System**: Windows 10/11, macOS, or Linux
- **Gemini API Key**: From Google AI Studio (required for Chat Assistant features)

---

## 2. Step-by-Step Installation

### Step 1: Clone Repository & Enter Directory
```powershell
git clone https://github.com/Praveen-Aj/GenshinIQ.git
cd GenshinIQ
```

### Step 2: Initialize Virtual Environment
```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS (Bash)
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

Edit `.env` with your preferred settings:
```ini
APP_NAME=GenshinIQ
APP_ENV=development
DEBUG=true
HOST=127.0.0.1
PORT=8000

# Your Default Genshin Impact UID (e.g., 817739968)
USER_UID=817739968

# Google Gemini API Key (Required for Phase 4 & 5 Chat Assistant)
GEMINI_API_KEY=your_gemini_api_key_here

# Enka.Network API Configuration
ENKA_API_BASE_URL=https://enka.network/api
ENKA_CACHE_TTL_SECONDS=300
```

---

## 3. Running the Application

### Option A: Using Convenience Scripts (Windows)
- **Start Web Application**: Run `scripts/run_server.bat` or `./scripts/run_server.ps1`
- **Run Automated Pytest Suite**: Run `scripts/run_tests.bat`
- **CLI Account Inspector**: Run `python scripts/import_account.py 817739968`

### Option B: Terminal Command (All Platforms)
```powershell
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
- **Web App**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc API**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 4. Running the Automated Test Suite

Execute the full pytest suite to verify system integrity:
```powershell
.venv\Scripts\pytest backend/tests -v
```

All 33 tests should pass:
- Enka normalizer & cache mechanics
- Canonical character, weapon, artifact, material queries
- Knowledge base search & source hierarchy
- Query intent classification & dynamic version context injection
- Health diagnostics & static file serving
- Provenance manifest generation and source/version summaries

Roadmap for the next release:
- [Next Version Roadmap](NEXT_VERSION_ROADMAP.md)

---

## 5. Troubleshooting & FAQ

| Issue | Cause | Solution |
|---|---|---|
| **`Gemini API Key is missing`** | `.env` file is missing `GEMINI_API_KEY` | Set a valid Google AI Studio key in `.env` and restart the server. |
| **`Connection timed out contacting Gemini API`** | Network latency or deep prompt | The timeout is set to 30s in `backend/services/gemini_service.py`. Ensure network allows outbound traffic to Google APIs. |
| **`Character not found in showcase`** | In-game showcase settings | Open Genshin Impact $\to$ Edit Profile $\to$ Ensure "Show Character Details" is toggled ON. |
| **Old CSS/JS loaded in browser** | Browser disk caching | Refresh with `Ctrl + F5` or append `?nocache=1` to the URL. Frontend links use automatic versioning strings. |
