# SafeSphere Deployment Without Docker

This guide deploys SafeSphere without Docker using:

- Python virtual environment
- systemd service for FastAPI
- Nginx for frontend and reverse proxy
- Optional Certbot SSL

---

## 1. Server Requirements

Recommended VPS:

- Ubuntu 22.04 or 24.04
- Python 3.11
- Node.js 20+
- Nginx
- 4 GB RAM minimum, more if the models are large
- GPU server if your model inference needs CUDA

Install basics:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git curl
```

Install Node.js using your preferred method, then confirm:

```bash
node -v
npm -v
```

---

## 2. Upload Project

Recommended path:

```txt
/var/www/safesphere
```

Example:

```bash
sudo mkdir -p /var/www/safesphere
sudo chown -R $USER:$USER /var/www/safesphere
```

Upload the project files into that folder.

---

## 3. Place Model Files

Use this structure:

```txt
/var/www/safesphere/models/
├── violence/
│   └── violence.weights.h5
└── toxicity/
    ├── toxic_model.pth
    ├── tokenizer/
    └── base_model/
```

---

## 4. Backend Setup

```bash
cd /var/www/safesphere/backend
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and use absolute paths:

```env
ALLOWED_ORIGINS=https://app.yourdomain.com
TOXICITY_MODEL_PATH=/var/www/safesphere/models/toxicity/toxic_model.pth
VIOLENCE_MODEL_PATH=/var/www/safesphere/models/violence/violence.weights.h5
TOXICITY_TOKENIZER_DIR=/var/www/safesphere/models/toxicity/tokenizer
TOXICITY_BASE_MODEL_DIR=/var/www/safesphere/models/toxicity/base_model
ENABLE_SHAP=false
```

Test backend manually:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

Open:

```txt
http://SERVER_IP:8000/health
```

Stop it with `CTRL+C` after testing.

---

## 5. Create systemd Service

Copy the included service file:

```bash
sudo cp /var/www/safesphere/deploy/systemd/safesphere-api.service /etc/systemd/system/safesphere-api.service
```

Make sure the paths inside the service match your project path.

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable safesphere-api
sudo systemctl start safesphere-api
sudo systemctl status safesphere-api
```

View logs:

```bash
sudo journalctl -u safesphere-api -f
```

---

## 6. Frontend Build

Set the production API URL before build:

```bash
cd /var/www/safesphere/frontend
cp .env.example .env
nano .env
```

For two domains:

```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

For a single-domain setup with `/api` proxy:

```env
VITE_API_BASE_URL=/api
```

Install and build:

```bash
npm install
npm run build
```

The static files will be inside:

```txt
/var/www/safesphere/frontend/dist
```

---

## 7. Nginx Setup

Two-domain setup:

```bash
sudo cp /var/www/safesphere/deploy/nginx/safesphere-no-docker.conf /etc/nginx/sites-available/safesphere
sudo ln -s /etc/nginx/sites-available/safesphere /etc/nginx/sites-enabled/safesphere
sudo nginx -t
sudo systemctl reload nginx
```

Single-domain setup:

```bash
sudo cp /var/www/safesphere/deploy/nginx/safesphere-single-domain.conf /etc/nginx/sites-available/safesphere
sudo ln -s /etc/nginx/sites-available/safesphere /etc/nginx/sites-enabled/safesphere
sudo nginx -t
sudo systemctl reload nginx
```

Remember to replace the placeholder domains in the Nginx config.

---

## 8. SSL with Certbot

After DNS points to the server:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx
```

---

## 9. Update Deployment

When you change backend code:

```bash
cd /var/www/safesphere/backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart safesphere-api
```

When you change frontend code:

```bash
cd /var/www/safesphere/frontend
npm install
npm run build
sudo systemctl reload nginx
```

---

## 10. Common Issues

### Backend starts then crashes

Check:

```bash
sudo journalctl -u safesphere-api -f
```

Most common causes:

- Wrong model path in `.env`
- Missing tokenizer or base model directory
- RAM is not enough
- Missing Python package

### Frontend cannot reach backend

Check:

- `frontend/.env` before `npm run build`
- `ALLOWED_ORIGINS` in `backend/.env`
- Nginx proxy config
- API domain SSL

### Text endpoint is slow

Set:

```env
ENABLE_SHAP=false
```

Then restart backend:

```bash
sudo systemctl restart safesphere-api
```
