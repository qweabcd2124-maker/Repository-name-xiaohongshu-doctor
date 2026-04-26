#!/bin/bash
set -e

echo "🚀 启动后端服务..."

cd backend

pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
