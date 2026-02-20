Write-Host "Starting Servers..." -ForegroundColor Green

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Backend running on http://localhost:8000"
Write-Host "Frontend running on http://localhost:5173 (default)"
