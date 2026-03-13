@echo off
title Parkify Backend Setup
color 0A

echo ==================================================
echo    PARKIFY - Backend Setup for Windows
echo ==================================================
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install Python 3.11+ from python.org
    echo    Make sure to check "Add Python to PATH" during install
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER% found
echo.

:: Create venv
if exist venv (
    echo [SKIP] Virtual environment already exists
) else (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv
        pause
        exit /b 1
    )
)

:: Activate and install
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat

pip install --upgrade pip --quiet
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 python-multipart==0.0.6 --quiet
:: Fixed bcrypt version to prevent passlib crashes
pip install python-jose[cryptography]==3.3.0 "passlib[bcrypt]==1.7.4" bcrypt==4.0.1 --quiet
pip install "pydantic[email]==2.5.3" pydantic-settings --quiet
:: Updated httpx to 0.28.1 to resolve firebase-admin conflict
pip install loguru==0.7.2 httpx==0.28.1 python-dotenv==1.0.0 --quiet
pip install websockets==12.0 --quiet
:: Consolidated firebase-admin installation
pip install firebase-admin --quiet

echo [3/3] Dependencies installed!
echo.

:: Seed Firebase
echo ==================================================
echo    Seeding Firebase with demo data...
echo ==================================================
python seed_firebase.py
echo.

:: Start server
echo ==================================================
echo    PARKIFY API SERVER
echo ==================================================
echo.
echo    API:        http://localhost:8000
echo    Docs:       http://localhost:8000/docs
echo    Dashboard:  http://localhost:8000/dashboard
echo.
echo    Demo Accounts:
echo       Admin: admin@parkify.com / admin123
echo       User:  amira@gmail.com   / user123
echo       User:  ahmed@gmail.com   / user123
echo       User:  sara@gmail.com    / user123
echo       User:  omar@gmail.com    / user123
echo.
echo    Press Ctrl+C to stop
echo ==================================================
echo.

python -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
pause
