#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../backend"
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Backend setup completed. Edit backend/.env before running the API."
