#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../frontend"
npm install

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Frontend setup completed. Edit frontend/.env if your backend URL is different."
