@echo off
title Launching Smart Meter Intelligence Platform...
echo ===================================================
echo   Smart Meter Intelligence Platform Startup Script
echo ===================================================
echo 1. Cleaning up unused vendor directories...
python scripts\cleanup_unused.py

echo.
echo 2. Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend npm packages...
    cd frontend
    call npm install
    cd ..
)

echo.
echo 2. Seeding demo dataset into database...
python scripts\seed_demo.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Seed script encountered an error or dependencies are missing. Proceeding...
)

echo.
echo 3. Launching FastAPI Backend Server on http://localhost:8000 ...
start "FastAPI Backend - Smart Meter Platform" cmd /k "uvicorn backend.app.main:app --reload --port 8000"

echo.
echo 4. Launching React Frontend Dashboard on http://localhost:3000 ...
start "React Dashboard - Smart Meter Platform" cmd /k "cd frontend && npm run dev"

echo.
echo Waiting 3 seconds for servers to start...
timeout /t 3 /nobreak >nul

echo.
echo Opening browser at http://localhost:3000 ...
start http://localhost:3000

echo ===================================================
echo   Platform started successfully!
echo   - Frontend: http://localhost:3000
echo   - Backend API Docs: http://localhost:8000/docs
echo ===================================================
pause
