Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Smart Meter Intelligence Platform Startup Script  " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Seeding demo database..." -ForegroundColor Yellow
python scripts/seed_demo.py

Write-Host ""
Write-Host "2. Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.app.main:app --reload --port 8000"

Write-Host ""
Write-Host "3. Starting React Frontend Dashboard on http://localhost:3000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm.cmd run dev"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Opening Firefox / default browser to http://localhost:3000 ..." -ForegroundColor Cyan
Start-Process "http://localhost:3000"
