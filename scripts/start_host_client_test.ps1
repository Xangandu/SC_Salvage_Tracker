# Startet zwei Salvage-Tracker-Instanzen zum Host/Client-Test.
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

Write-Host "Starte Host-Instanz in neuem Fenster..."
Write-Host "  -> Modus: Host, anmelden, warten bis 'HOST' in der Leiste steht"
Start-Process py -ArgumentList "-3", "main.py" -WorkingDirectory $ProjectRoot

Write-Host "Warte 15 Sekunden (Zeit fuer Host-Login)..."
Start-Sleep -Seconds 15

Write-Host "Starte Client-Instanz..."
Write-Host "  -> Modus: Client, 127.0.0.1:47890, Beitrittscode vom Host"
py -3 main.py
