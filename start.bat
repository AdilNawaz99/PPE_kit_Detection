@echo off
REM Quick Start Script for PPE Detection Dashboard on Windows

echo.
echo ====================================
echo PPE DETECTION DASHBOARD - QUICK START
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo [1/5] Installing backend dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo [2/5] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo [3/5] Opening terminal for backend...
start cmd /k "cd backend && python app.py"

timeout /t 3 /nobreak

echo.
echo [4/5] Opening terminal for frontend...
start cmd /k "cd frontend && npm start"

echo.
echo ====================================
echo DASHBOARD STARTED!
echo ====================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Frontend will open automatically in your browser.
echo Check the terminals for any errors.
echo.
echo Press CTRL+C in each terminal to stop.
echo.
pause
