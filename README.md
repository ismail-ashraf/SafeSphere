# SafeSphere No-Docker Edition

SafeSphere is an AI moderation dashboard and API for:

- Image violence detection
- Toxic text detection
- Combined image + text moderation

This version is prepared **without Docker**. It uses:

- FastAPI backend
- React + Vite frontend
- Python virtual environment for backend
- Static frontend build for deployment
- Optional systemd + Nginx deployment on VPS

---

## Project Structure

```txt
SafeSphere-no-docker/
├── backend/
│   ├── main.py
│   ├── models/
│   ├── requirements.txt
│   ├── .env.example
│   ├── Procfile
│   └── runtime.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── .env.example
│   ├── vercel.json
│   └── netlify.toml
├── models/
│   ├── violence/
│   └── toxicity/
├── deploy/
│   ├── nginx/
│   └── systemd/
├── scripts/
└── docs/
```

---

## Required Model Files

Before running the backend, place your model files like this:

```txt
models/
├── violence/
│   └── violence.weights.h5
└── toxicity/
    ├── toxic_model.pth
    ├── tokenizer/
    └── base_model/
```

Then edit:

```txt
backend/.env
```

Default local paths are already prepared in `backend/.env.example`.

---

## Run Locally on Windows

### 1. Backend

From PowerShell in the project root:

```powershell
.\scripts\setup_backend_windows.ps1
.\scripts\run_backend_windows.ps1
```

Backend URL:

```txt
http://localhost:8000
```

API docs:

```txt
http://localhost:8000/docs
```

### 2. Frontend

Open another PowerShell window:

```powershell
.\scripts\setup_frontend_windows.ps1
.\scripts\run_frontend_windows.ps1
```

Frontend URL:

```txt
http://localhost:5173
```

---

## Run Locally on Linux / macOS

```bash
./scripts/setup_backend_linux.sh
./scripts/run_backend_linux.sh
```

In another terminal:

```bash
./scripts/setup_frontend_linux.sh
./scripts/run_frontend_linux.sh
```

---

## Manual Backend Commands

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Manual Frontend Commands

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

To create a production frontend build:

```bash
npm run build
```

The production files will be generated in:

```txt
frontend/dist/
```

---

## Deployment Without Docker

Read the full guide here:

```txt
docs/NO_DOCKER_DEPLOYMENT.md
```

Recommended production setup:

```txt
Frontend static build → Nginx
Backend FastAPI → Python venv + systemd
Reverse proxy → Nginx
SSL → Certbot
```

---

## Main API Endpoints

```txt
GET  /health
POST /predict/text
POST /predict/image
POST /predict/combined
```

See:

```txt
docs/API_CONTRACT.md
```

---

## Important Notes

- This version intentionally has no Docker files.
- `ENABLE_SHAP=false` is recommended at first because SHAP can slow down text inference.
- Keep model files outside Git if they are large.
- For production, use absolute model paths in `backend/.env`.
