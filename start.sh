#!/bin/bash

echo "=========================================="
echo "   PARKIFY - Local Development Setup"
echo "=========================================="
echo ""

# Check Python version
PYTHON_CMD=""

# Try python3.11 first (recommended)
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "✅ Found Python 3.11"
# Try python3.12
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "✅ Found Python 3.12"
# Try python3.13
elif command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
    echo "✅ Found Python 3.13"
# Try generic python3
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VER=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "✅ Found Python $PYTHON_VER"
    
    # Warning for Python 3.14+
    if [[ "$PYTHON_VER" == "3.14" ]]; then
        echo ""
        echo "⚠️  WARNING: Python 3.14 detected!"
        echo "    Some packages may not work. Recommended: Python 3.11 or 3.12"
        echo ""
    fi
else
    echo "❌ Python3 not found!"
    echo "   Install Python 3.11: sudo apt install python3.11 python3.11-venv"
    exit 1
fi

echo "   Using: $PYTHON_CMD"
echo ""

# Remove old venv if exists
if [ -d "venv" ]; then
    echo "[0/4] Removing old virtual environment..."
    rm -rf venv
fi

echo "[1/4] Creating virtual environment..."
$PYTHON_CMD -m venv venv

echo "[2/4] Activating virtual environment..."
source venv/bin/activate

echo "[3/4] Upgrading pip and installing dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn[standard] python-multipart
pip install python-jose[cryptography] passlib[bcrypt]
pip install pydantic pydantic-settings
pip install loguru httpx python-dotenv websockets

echo "[4/4] Starting server..."
echo ""
echo "=========================================="
echo "   🅿️  PARKIFY API SERVER"
echo "=========================================="
echo ""
echo "   🌐 API:  http://localhost:8000"
echo "   📚 Docs: http://localhost:8000/docs"
echo ""
echo "   👤 Demo Accounts:"
echo "      Admin: admin@parkify.com / admin123"
echo "      User:  user@parkify.com / user123"
echo ""
echo "   Press Ctrl+C to stop"
echo "=========================================="
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
