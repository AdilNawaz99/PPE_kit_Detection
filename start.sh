#!/bin/bash
# Quick Start Script for PPE Detection Dashboard on Linux/Mac

echo ""
echo "===================================="
echo "PPE DETECTION DASHBOARD - QUICK START"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

echo "[1/5] Installing backend dependencies..."
cd backend
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install backend dependencies"
    exit 1
fi
cd ..

echo ""
echo "[2/5] Installing frontend dependencies..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install frontend dependencies"
    exit 1
fi
cd ..

echo ""
echo "[3/5] Starting backend server..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

sleep 3

echo ""
echo "[4/5] Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

sleep 3

echo ""
echo "===================================="
echo "DASHBOARD STARTED!"
echo "===================================="
echo ""
echo "Backend:  http://localhost:5000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Frontend will open automatically in your browser."
echo ""
echo "To stop:"
echo "  kill $BACKEND_PID  (backend)"
echo "  kill $FRONTEND_PID (frontend)"
echo ""

# Wait for user input
read -p "Press Enter to stop..."

kill $BACKEND_PID
kill $FRONTEND_PID
