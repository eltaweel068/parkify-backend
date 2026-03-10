#!/bin/bash

echo "=========================================="
echo "   PARKIFY - Backend Setup (Linux/Mac)"
echo "=========================================="
echo ""

# Check Python version
PYTHON_CMD=""

if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "[OK] Found Python 3.11"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "[OK] Found Python 3.12"
elif command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
    echo "[OK] Found Python 3.13"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VER=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "[OK] Found Python $PYTHON_VER"
else
    echo "[ERROR] Python3 not found!"
    echo "   Install: sudo apt install python3 python3-venv"
    exit 1
fi

echo "   Using: $PYTHON_CMD"
echo ""

# Create venv if not exists
if [ -d "venv" ]; then
    echo "[SKIP] Virtual environment already exists"
else
    echo "[1/3] Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

echo "[2/3] Installing dependencies..."
source venv/bin/activate

pip install --upgrade pip -q
pip install fastapi==0.109.0 "uvicorn[standard]==0.27.0" python-multipart==0.0.6 -q
pip install "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" -q
pip install "pydantic[email]==2.5.3" pydantic-settings==2.1.0 -q
pip install loguru==0.7.2 httpx==0.26.0 python-dotenv==1.0.0 -q
pip install websockets==12.0 -q
pip install firebase-admin -q

echo "[3/3] Dependencies installed!"
echo ""

# Seed Firebase
echo "=========================================="
echo "   Seeding Firebase with demo data..."
echo "=========================================="
python seed_firebase.py
echo ""

# Start server
echo "=========================================="
echo "   PARKIFY API SERVER"
echo "=========================================="
echo ""
echo "   API:       http://localhost:8000"
echo "   Docs:      http://localhost:8000/docs"
echo "   Dashboard: http://localhost:8000/dashboard"
echo ""
echo "   Demo Accounts:"
echo "      Admin: admin@parkify.com / admin123"
echo "      User:  amira@gmail.com   / user123"
echo "      User:  ahmed@gmail.com   / user123"
echo "      User:  sara@gmail.com    / user123"
echo "      User:  omar@gmail.com    / user123"
echo ""
echo "   Press Ctrl+C to stop"
echo "=========================================="
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
