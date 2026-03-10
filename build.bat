@echo off
REM ============================================================
REM  Fabric Real-Time Data Generator — Windows build script
REM  Produces a single-file .exe in dist\FabricRTDG.exe
REM
REM  Prerequisites (run once):
REM    pip install -r requirements.txt
REM    pip install pyinstaller
REM ============================================================

setlocal

echo.
echo =========================================
echo  Fabric Real-Time Data Generator Builder
echo =========================================
echo.

REM ── Locate Python ───────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo Python: %%i

REM ── Check / install PyInstaller ─────────────────────────────
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller not found. Installing…
    python -m pip install pyinstaller --quiet
)

REM ── Check requirements ──────────────────────────────────────
echo [INFO] Installing / verifying requirements…
python -m pip install -r requirements.txt --quiet

REM ── Clean previous build ────────────────────────────────────
if exist "dist\FabricRTDG.exe" (
    echo [INFO] Removing previous dist\FabricRTDG.exe…
    del /q "dist\FabricRTDG.exe"
)
if exist "build" (
    echo [INFO] Removing build\ cache…
    rmdir /s /q "build"
)

REM ── Build ───────────────────────────────────────────────────
echo.
echo [INFO] Running PyInstaller…
python -m PyInstaller fabric_rtdg.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check output above for details.
    pause
    exit /b 1
)

echo.
echo =========================================
echo  BUILD COMPLETE
echo  Output: dist\FabricRTDG.exe
echo =========================================
echo.

REM ── Optional: open the dist folder ─────────────────────────
if exist "dist\FabricRTDG.exe" (
    echo [INFO] Opening dist folder…
    explorer dist
)

endlocal
pause
