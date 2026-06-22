@echo off
chcp 65001 >nul
setlocal

REM SC Salvage Tracker — Entwicklungsumgebung einrichten (ohne PowerShell ExecutionPolicy)
cd /d "%~dp0.."

echo.
echo  SC Salvage Tracker — Setup Entwicklungsumgebung
echo  ================================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python Launcher "py" nicht gefunden.
    echo Bitte Python 3.11+ von https://www.python.org/downloads/ installieren.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Erstelle virtuelle Umgebung .venv ...
    py -3 -m venv .venv
    if errorlevel 1 exit /b 1
)

echo Installiere Abhaengigkeiten in .venv ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo Optional: UPnP-Bibliothek ...
".venv\Scripts\python.exe" -m pip install -r requirements-optional.txt
echo.

echo ================================================
echo  Setup abgeschlossen.
echo.
echo  Tracker starten:
echo    scripts\run_tracker.bat
echo.
echo  Oder in CMD (ohne PowerShell-Policy):
echo    .venv\Scripts\activate.bat
echo    python main.py
echo ================================================
echo.
pause
