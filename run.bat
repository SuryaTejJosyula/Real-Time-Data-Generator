@echo off
REM ============================================================
REM  Fabric Real-Time Data Generator — Launcher
REM
REM  Requirements: Python 3.10 or newer must be on your PATH.
REM  Download Python from https://www.python.org/downloads/
REM  (check "Add Python to PATH" during install)
REM ============================================================

setlocal

echo.
echo  ==========================================
echo   Fabric Real-Time Data Generator
echo  ==========================================
echo.

REM ── Verify Python is available ──────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found on PATH.
    echo  Install Python 3.10+ from https://www.python.org/downloads/
    echo  and make sure to tick "Add Python to PATH" during setup.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  Found: %%v

REM ── Create / reuse a local virtual environment ──────────────
if not exist ".venv\Scripts\activate.bat" (
    echo  [INFO] Creating virtual environment…
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM ── Install / update dependencies ───────────────────────────
echo  [INFO] Installing dependencies (first run may take a minute)…
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

REM ── Launch the app ──────────────────────────────────────────
echo  [INFO] Starting app…
echo.
python main.py

REM ── Keep window open if the app exits with an error ─────────
if errorlevel 1 (
    echo.
    echo  [ERROR] The app exited with an error. See output above.
    pause
)
