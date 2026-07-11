# Bereitet Installer-Grafiken aus splash.png vor.
# Nutzung: powershell -ExecutionPolicy Bypass -File installer\prepare_installer_assets.ps1

$ErrorActionPreference = "Stop"

$InstallerDir = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $InstallerDir
$Splash = Join-Path $ProjectRoot "assets\images\splash.png"

if (-not (Test-Path $Splash)) {
    throw "Splash-Bild nicht gefunden: $Splash"
}

Write-Host "Erzeuge Launcher-Installer-Grafiken..."
py -3 (Join-Path $InstallerDir "sync_app_icon.py")
if ($LASTEXITCODE -ne 0) {
    throw "App-Icon-Sync fehlgeschlagen. Bitte assets/images/scst_solo_logo.ico ablegen."
}
py -3 (Join-Path $InstallerDir "generate_installer_assets.py")
