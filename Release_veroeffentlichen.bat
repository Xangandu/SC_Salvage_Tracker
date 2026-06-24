@echo off
title SC Salvage Tracker - Release (vollautomatisch)
cd /d "%~dp0"

echo.
echo  Starte vollautomatischen Release...
echo  Keine Eingaben noetig - Fenster offen lassen bis Fertig.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\release_auto.ps1"

echo.
if errorlevel 1 (
  echo  FEHLER - Release abgebrochen. Meldung oben lesen.
) else (
  echo  Erfolgreich abgeschlossen.
)
echo.
pause
exit /b %ERRORLEVEL%
