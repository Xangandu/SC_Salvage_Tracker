@echo off
cd /d "%~dp0"
start "SC Salvage Tracker - Release" powershell.exe -ExecutionPolicy Bypass -File "%~dp0Release_veroeffentlichen.ps1"
exit /b 0
