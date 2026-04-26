#!/bin/bash

cd backend

pip install -r requirements.txt

exec python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
