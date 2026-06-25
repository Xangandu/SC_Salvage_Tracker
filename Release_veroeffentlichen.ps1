# SC Salvage Tracker - Release Launcher (blaues PowerShell-Fenster)
$Host.UI.RawUI.WindowTitle = "SC Salvage Tracker - Release"

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " SC Salvage Tracker - Vollautomatischer Release" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starte Release..." -ForegroundColor White
Write-Host "Keine Eingaben noetig - Fenster offen lassen bis Fertig." -ForegroundColor DarkGray
Write-Host ""

$script = Join-Path $PSScriptRoot "installer\release_auto.ps1"
& $script
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -ne 0) {
    Write-Host "FEHLER - Release abgebrochen. Meldung oben lesen." -ForegroundColor Red
}
else {
    Write-Host "Erfolgreich abgeschlossen." -ForegroundColor Green
}
Write-Host ""
Read-Host "Enter zum Schliessen"
exit $exitCode
