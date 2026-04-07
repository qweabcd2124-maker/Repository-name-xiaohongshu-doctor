#!/bin/bash
# 薯医 NoteRx 一键启动脚本
# Usage: ./start.sh

set -e

echo "💊 薯医 NoteRx 启动中..."

# Check .env
if [ ! -f backend/.env ] && [ ! -f .env ]; then
  echo "⚠️  未找到 .env 文件，请复制 .env.example 并填入 API Key"
  echo "   cp .env.example backend/.env"
fi

# Start backend
echo "🔧 启动后端服务..."
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -q
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start frontend
echo "🎨 启动前端服务..."
cd frontend
npm install -q 2>/dev/null
npx vite --port 5173 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ 薯医 NoteRx 已启动！"
echo "   前端: http://localhost:5173"
echo "   后端: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
