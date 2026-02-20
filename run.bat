@echo off
echo Starting Backend Server...
start "Backend Server" cmd /k "uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

echo Starting Frontend Server...
cd frontend
start "Frontend Server" cmd /k "npm run dev"
cd ..

echo Servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
