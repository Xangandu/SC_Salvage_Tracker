# SC Salvage Tracker - Installer bauen (MobiGlas Custom Setup)
#
# Ergebnis:
#   ..\..\..\Release\app\SC_Salvage_Tracker\
#   ..\..\..\Release\installer\SC_Salvage_Tracker_Setup_0.9.0.exe
#
# Nutzung:
#   powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
#   powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -SkipInno
#   powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -SkipPyInstaller

param(
    [switch]$SkipInno,
    [switch]$SkipPyInstaller
)

$ErrorActionPreference = "Stop"

$InstallerDir = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $InstallerDir
$ScRoot = Split-Path -Parent (Split-Path -Parent $ProjectRoot)
$ReleaseRoot = Join-Path $ScRoot "Release"
$AppOutput = Join-Path $ReleaseRoot "app\SC_Salvage_Tracker"
$InstallerOutput = Join-Path $ReleaseRoot "installer"

function Get-VersionMeta {
    param([string]$VersionFile)
    $content = Get-Content $VersionFile -Raw
    $meta = @{
        FileVersion = "0.14.1"
        DisplayVersion = "0.14.1 Alpha"
        Build = "2026.06"
        Codename = "Launcher Polish"
    }

    if ($content -match 'APP_VERSION\s*=\s*"([^"]+)"') {
        $meta.DisplayVersion = $Matches[1].Trim()
        $meta.FileVersion = ($Matches[1] -replace '\s+(Alpha|Beta|RC\d*)\s*$', '').Trim()
    }
    if ($content -match 'APP_BUILD\s*=\s*"([^"]+)"') {
        $meta.Build = $Matches[1].Trim()
    }
    if ($content -match 'APP_CODENAME\s*=\s*"([^"]+)"') {
        $meta.Codename = $Matches[1].Trim()
    }

    return $meta
}

function Stop-RunningApp {
    $processNames = @(
        "SC_Salvage_Tracker",
        "SC_Salvage_Tracker.exe"
    )
    foreach ($name in $processNames) {
        Get-Process -Name $name -ErrorAction SilentlyContinue |
            Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

function Remove-DirSafe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [int]$Retries = 4
    )

    if (-not (Test-Path $Path)) {
        return $true
    }

    for ($attempt = 1; $attempt -le $Retries; $attempt++) {
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            return $true
        }
        catch {
            if ($attempt -lt $Retries) {
                Write-Host "  $Label gesperrt (Versuch $attempt/$Retries), warte 2 Sekunden..."
                Start-Sleep -Seconds 2
            }
        }
    }

    Write-Warning "Konnte $Label nicht loeschen: $Path"
    Write-Warning "Datei wird von einem anderen Prozess verwendet."
    Write-Warning "Bitte SC Salvage Tracker beenden und Explorer-Fenster im Projekt schliessen."
    return $false
}

$VersionMeta = Get-VersionMeta (Join-Path $ProjectRoot "config\version.py")
$AppVersion = $VersionMeta.FileVersion
$AppVersionDisplay = $VersionMeta.DisplayVersion
$AppBuild = $VersionMeta.Build
$AppCodename = $VersionMeta.Codename
$AppVersionInfo = $AppVersion
if ($AppVersionInfo -notmatch '^\d+\.\d+\.\d+\.\d+$') {
    $parts = @($AppVersionInfo -split '\.')
    while ($parts.Count -lt 4) {
        $parts += '0'
    }
    $AppVersionInfo = ($parts[0..3] -join '.')
}

Write-Host "Projekt:   $ProjectRoot"
Write-Host "Release:   $ReleaseRoot"
Write-Host "Version:   $AppVersionDisplay (Build $AppBuild · $AppCodename)"
Write-Host ""

Set-Location $ProjectRoot

Write-Host "Installer-Grafiken vorbereiten..."
& (Join-Path $InstallerDir "prepare_installer_assets.ps1")

if (-not $SkipPyInstaller) {
    Write-Host "Installiere Python-Abhaengigkeiten..."
    py -3 -m pip install -r requirements.txt --quiet

    $OptionalReq = Join-Path $ProjectRoot "requirements-optional.txt"
    if (Test-Path $OptionalReq) {
        Write-Host "Optional: UPnP (miniupnpc)..."
        & py -3 -m pip install -r $OptionalReq --quiet 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Hinweis: miniupnpc nicht installiert (UPnP optional, Build laeuft weiter)."
            Write-Host "  Grund oft: kein C++-Build-Tool oder kein Wheel fuer diese Python-Version."
        }
    }

    Write-Host "Bereinige alte Build-Artefakte..."
    Stop-RunningApp
    Start-Sleep -Milliseconds 800

    $buildDir = Join-Path $ProjectRoot "build"
    $distDir = Join-Path $ProjectRoot "dist"

    Remove-DirSafe -Path $buildDir -Label "build-Ordner" | Out-Null
    Remove-DirSafe -Path $distDir -Label "dist-Ordner" | Out-Null
    Remove-DirSafe -Path $AppOutput -Label "Release-App-Ordner" | Out-Null

    New-Item -ItemType Directory -Force -Path $AppOutput | Out-Null

    Write-Host "PyInstaller starten..."
    py -3 -m PyInstaller `
        --noconfirm `
        --clean `
        (Join-Path $InstallerDir "salvage_tracker.spec")

    $DistApp = Join-Path $ProjectRoot "dist\SC_Salvage_Tracker"
    if (-not (Test-Path $DistApp)) {
        throw "PyInstaller-Ausgabe nicht gefunden: $DistApp"
    }

    Write-Host "Kopiere App nach Release..."
    Copy-Item -Path (Join-Path $DistApp "*") -Destination $AppOutput -Recurse -Force

    Write-Host ""
    Write-Host "App-Build fertig: $AppOutput"
}
else {
    if (-not (Test-Path $AppOutput)) {
        throw "App-Ordner fehlt: $AppOutput (ohne -SkipPyInstaller bauen)"
    }
    Write-Host "PyInstaller uebersprungen, vorhandener App-Build: $AppOutput"
}

New-Item -ItemType Directory -Force -Path $InstallerOutput | Out-Null

if ($SkipInno) {
    Write-Host "Inno Setup uebersprungen (-SkipInno)."
    exit 0
}

$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Iscc) {
    Write-Host ""
    Write-Host "HINWEIS: Inno Setup 6 nicht gefunden."
    Write-Host "Die App liegt fertig unter: $AppOutput"
    Write-Host "Installiere Inno Setup 6.7+ und fuehre danach aus:"
    $IssPath = Join-Path $InstallerDir "sc_salvage_tracker.iss"
    Write-Host ('  "{0}" /DMyAppVersion={1} "{2}"' -f $IsccCandidates[0], $AppVersion, $IssPath)
    exit 0
}

$IssFile = Join-Path $InstallerDir "sc_salvage_tracker.iss"
$SetupName = "SC_Salvage_Tracker_Setup_$AppVersion.exe"
$StageDir = Join-Path $env:TEMP ("SC_Salvage_Tracker_installer_build_" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

Write-Host "Inno Setup starten (SC Salvage Tracker Custom Setup)..."
Write-Host "Staging (Temp-Ordner): $StageDir"
& $Iscc `
    "/DMyAppVersion=$AppVersionDisplay" `
    "/DMyAppVersionFile=$AppVersion" `
    "/DMyAppVersionInfo=$AppVersionInfo" `
    "/DMyAppBuild=$AppBuild" `
    "/DMyAppCodename=$AppCodename" `
    "/DInstallerOutputDir=$StageDir" `
    $IssFile

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup fehlgeschlagen (Exit-Code $LASTEXITCODE). Setup-EXE schliessen oder Antivirus-Ausnahme fuer Release\installer setzen."
}

$BuiltExe = Join-Path $StageDir $SetupName
if (-not (Test-Path $BuiltExe)) {
    throw "Setup-EXE nicht gefunden nach Build: $BuiltExe"
}

$SetupExe = Join-Path $InstallerOutput $SetupName
$Copied = $false

for ($attempt = 1; $attempt -le 5; $attempt++) {
    try {
        if (Test-Path $SetupExe) {
            Remove-Item $SetupExe -Force -ErrorAction Stop
        }
        Copy-Item -Path $BuiltExe -Destination $SetupExe -Force -ErrorAction Stop
        $Copied = $true
        break
    }
    catch {
        if ($attempt -lt 5) {
            Write-Host "Kopieren nach Release blockiert (Versuch $attempt/5), warte 2 Sekunden..."
            Start-Sleep -Seconds 2
        }
    }
}

if (-not $Copied) {
    Write-Warning "Konnte Setup nicht nach Release kopieren (Datei gesperrt / Antivirus?)."
    Write-Warning "Die fertige EXE liegt hier: $BuiltExe"
    exit 1
}

Write-Host ""
Write-Host "Fertig!"
Write-Host "Setup-EXE: $SetupExe"
