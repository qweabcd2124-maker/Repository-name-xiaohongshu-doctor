#!/bin/bash

# 启动 backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
cd ..

# 启动 frontend（打包）
cd frontend
npm install
npm run build

# 用简单静态服务器跑前端
npm install -g serve
serve -s dist -l $PORT
