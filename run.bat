@echo off
echo Starting Backend...
start cmd /k "call .venv\Scripts\activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

echo Starting Frontend...
start cmd /k "cd frontend && npm run dev"

echo Services started.
