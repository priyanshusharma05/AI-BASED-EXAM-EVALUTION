# Deployment notes (FastAPI)

This document describes the minimal steps to run the backend without Docker.

Prerequisites
- Python 3.11
- MongoDB reachable (local or remote)

Environment variables (copy `.env.example` to `.env` and edit):
- `MONGODB_URI` - MongoDB connection string
- `DB_NAME` - Database name (default `exam_system`)
- `BASE_URL` - Public URL where backend will be served (used in generated file URLs)
- `FRONTEND_BASE_URL` - Frontend base URL for redirects
- `UPLOAD_FOLDER` - Path to uploads directory (default `./uploads`)
- `GEMINI_API_KEY` - (optional) AI extraction key

Run locally (PowerShell):

```powershell
cd d:\Final\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:MONGODB_URI = 'mongodb://localhost:27017/'
$env:DB_NAME = 'exam_system'
$env:BASE_URL = 'http://127.0.0.1:5000'
uvicorn fastapi_app:app --host 127.0.0.1 --port 5000
```

Migration (rename upload folders to lowercase)
1. Backup DB: `mongodump --uri "$MONGODB_URI" --db "$DB_NAME"`
2. Backup uploads folder: copy the `uploads` directory to a safe location.
3. Dry-run: `python migrations/rename_upload_paths.py --dry-run`
4. If dry-run looks good: `python migrations/rename_upload_paths.py --apply`

CI
- A GitHub Actions workflow is provided at `.github/workflows/ci.yml`. It runs on Ubuntu, installs dependencies, starts MongoDB and the FastAPI server on the runner, and performs smoke tests.

Notes
- This setup intentionally avoids Docker for simplicity.
- For production consider running under systemd, using a process manager (gunicorn + uvicorn workers), and configuring TLS/reverse proxy (nginx).
