# SC Salvage Tracker - Installer bauen (MobiGlas Custom Setup)
#
# Ergebnis (Beispiel SOLO):
#   ..\..\..\Release\app\SC_Salvage_Tracker_SOLO\
#   ..\..\..\Release\installer\SC_Salvage_Tracker_Setup_SOLO_0.16.0.exe
#
# Nutzung:
#   powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1
#   powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition crew
#   powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -Edition all
#   powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -SkipInno
#   powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1 -UseInno

param(
    [ValidateSet("solo", "crew", "orga", "all")]
    [string]$Edition = "solo",
    [switch]$SkipInno,
    [switch]$SkipPyInstaller,
    [switch]$UseInno
)

$ErrorActionPreference = "Stop"

$InstallerDir = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $InstallerDir
$ScRoot = Split-Path -Parent (Split-Path -Parent $ProjectRoot)
$ReleaseRoot = Join-Path $ScRoot "Release"
$InstallerOutput = Join-Path $ReleaseRoot "installer"
$BuildEditionFile = Join-Path $ProjectRoot "config\build_edition.txt"
$SpecFile = Join-Path $InstallerDir "salvage_tracker.spec"
$IssFile = Join-Path $InstallerDir "sc_salvage_tracker.iss"

$EditionProfiles = @{
    solo = @{
        Key = "solo"
        AppName = "SC Salvage Tracker - SOLO Version"
        AppId = "A7C3E9F1-2B4D-4E8A-9F1C-6D5E8A2B4C7F"
        SetupSuffix = "SOLO"
        AppFolder = "SC_Salvage_Tracker_SOLO"
    }
    crew = @{
        Key = "crew"
        AppName = "SC Salvage Tracker - CREW Version"
        AppId = "B8D4F0A2-3C5E-4F9B-0A2D-7E6F9B3C5D8E"
        SetupSuffix = "CREW"
        AppFolder = "SC_Salvage_Tracker_CREW"
    }
    orga = @{
        Key = "orga"
        AppName = "SC Salvage Tracker - ORGA Version"
        AppId = "C9E5A1B3-4D6F-501C-1B3E-8F7A0C4D6E9F"
        SetupSuffix = "ORGA"
        AppFolder = "SC_Salvage_Tracker_ORGA"
    }
}

function Get-VersionMeta {
    param([string]$VersionFile)
    $content = Get-Content $VersionFile -Raw
    $meta = @{
        FileVersion = "0.16.0"
        DisplayVersion = "0.16.0 Beta"
        Build = "2026.11"
        Codename = "LOCATION FLOW"
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

function Set-BuildEditionMarker {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EditionKey
    )

    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($BuildEditionFile, $EditionKey, $utf8NoBom)
    Write-Host "Build-Edition: $EditionKey -> $BuildEditionFile"
}

function Build-AppBundle {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Profile,
        [Parameter(Mandatory = $true)]
        [string]$AppOutput
    )

    Set-BuildEditionMarker -EditionKey $Profile.Key

    Write-Host "Installiere Python-Abhaengigkeiten..."
    py -3 -m pip install -r (Join-Path $ProjectRoot "requirements.txt") --quiet

    $OptionalReq = Join-Path $ProjectRoot "requirements-optional.txt"
    if (Test-Path $OptionalReq) {
        Write-Host "Optional: UPnP (miniupnpc)..."
        & py -3 -m pip install -r $OptionalReq --quiet 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Hinweis: miniupnpc nicht installiert (UPnP optional, Build laeuft weiter)."
        }
    }

    Write-Host "Bereinige alte Build-Artefakte ($($Profile.SetupSuffix))..."
    Stop-RunningApp
    Start-Sleep -Milliseconds 800

    $buildDir = Join-Path $ProjectRoot "build"
    $distDir = Join-Path $ProjectRoot "dist"

    Remove-DirSafe -Path $buildDir -Label "build-Ordner" | Out-Null
    Remove-DirSafe -Path $distDir -Label "dist-Ordner" | Out-Null
    Remove-DirSafe -Path $AppOutput -Label "Release-App-Ordner" | Out-Null

    New-Item -ItemType Directory -Force -Path $AppOutput | Out-Null

    Write-Host "PyInstaller starten ($($Profile.AppName))..."
    py -3 -m PyInstaller --noconfirm --clean $SpecFile

    $DistApp = Join-Path $ProjectRoot "dist\SC_Salvage_Tracker"
    if (-not (Test-Path $DistApp)) {
        throw "PyInstaller-Ausgabe nicht gefunden: $DistApp"
    }

    Write-Host "Kopiere App nach Release..."
    Copy-Item -Path (Join-Path $DistApp "*") -Destination $AppOutput -Recurse -Force
    Write-Host "App-Build fertig: $AppOutput"
}

function Build-InnoSetup {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Profile,
        [Parameter(Mandatory = $true)]
        [string]$AppOutput,
        [Parameter(Mandatory = $true)]
        [hashtable]$VersionMeta
    )

    $IsccCandidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    $Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $Iscc) {
        Write-Host ""
        Write-Host "HINWEIS: Inno Setup 6 nicht gefunden."
        Write-Host "Die App liegt fertig unter: $AppOutput"
        return $null
    }

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

    $SetupName = "SC_Salvage_Tracker_Setup_$($Profile.SetupSuffix)_$AppVersion.exe"
    $StageDir = Join-Path $env:TEMP ("SC_Salvage_Tracker_installer_" + $Profile.Key + "_" + [guid]::NewGuid().ToString("N").Substring(0, 8))
    New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

    $AppOutputRelative = "..\..\..\Release\app\$($Profile.AppFolder)"
    $AppIdDefine = "{{$($Profile.AppId)}}"
    Write-Host "Inno Setup ($($Profile.SetupSuffix))..."
    & $Iscc `
        "/DMyAppVersion=$AppVersionDisplay" `
        "/DMyAppVersionFile=$AppVersion" `
        "/DMyAppVersionInfo=$AppVersionInfo" `
        "/DMyAppBuild=$AppBuild" `
        "/DMyAppCodename=$AppCodename" `
        "/DMyAppEdition=$($Profile.Key)" `
        "/DMyAppName=$($Profile.AppName)" `
        "/DMyAppId=$AppIdDefine" `
        "/DMyAppOutputFolder=$AppOutputRelative" `
        "/DMyAppSetupSuffix=$($Profile.SetupSuffix)" `
        "/DInstallerOutputDir=$StageDir" `
        $IssFile

    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup fehlgeschlagen fuer $($Profile.SetupSuffix) (Exit-Code $LASTEXITCODE)."
    }

    $BuiltExe = Join-Path $StageDir $SetupName
    if (-not (Test-Path $BuiltExe)) {
        throw "Setup-EXE nicht gefunden: $BuiltExe"
    }

    New-Item -ItemType Directory -Force -Path $InstallerOutput | Out-Null
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
                Write-Host "Kopieren blockiert (Versuch $attempt/5), warte 2 Sekunden..."
                Start-Sleep -Seconds 2
            }
        }
    }

    if (-not $Copied) {
        Write-Warning "Konnte Setup nicht nach Release kopieren: $SetupExe"
        Write-Warning "Fertige EXE: $BuiltExe"
        return $null
    }

    Write-Host "Setup-EXE: $SetupExe"

    $ManifestScript = Join-Path $InstallerDir "generate_update_manifest.py"
    $ManifestPath = Join-Path $InstallerOutput ("update-manifest-" + $Profile.Key + ".json")
    & py -3 $ManifestScript `
        --setup $SetupExe `
        --output $ManifestPath `
        --tag "v$AppVersion" `
        --edition $Profile.Key `
        --app-name $Profile.AppName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Update-Manifest: $ManifestPath"
        if ($Profile.Key -eq "solo") {
            $DefaultManifest = Join-Path $InstallerOutput "update-manifest.json"
            Copy-Item -Path $ManifestPath -Destination $DefaultManifest -Force
            Write-Host "Standard-Manifest: $DefaultManifest"
        }
    }

    return $SetupExe
}

function Build-PySideSetup {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Profile,
        [Parameter(Mandatory = $true)]
        [string]$AppOutput,
        [Parameter(Mandatory = $true)]
        [hashtable]$VersionMeta
    )

    $AppVersion = $VersionMeta.FileVersion
    $SetupName = "SC_Salvage_Tracker_Setup_$($Profile.SetupSuffix)_$AppVersion.exe"
    $PayloadZip = Join-Path $InstallerDir "payload_$($Profile.Key).zip"
    $SetupSpec = Join-Path $InstallerDir "setup_wizard.spec"
    $EditionDist = Join-Path $ProjectRoot "dist\setup_$($Profile.Key)"

    Write-Host "Erstelle Payload-ZIP ($($Profile.SetupSuffix))..."
    if (Test-Path $PayloadZip) {
        Remove-Item $PayloadZip -Force
    }
    Compress-Archive -Path (Join-Path $AppOutput '*') -DestinationPath $PayloadZip -CompressionLevel Optimal -Force

    Remove-DirSafe -Path $EditionDist -Label "Setup-Dist" | Out-Null
    New-Item -ItemType Directory -Force -Path $EditionDist | Out-Null

    $env:SST_SETUP_EDITION = $Profile.Key
    Write-Host "PyInstaller Setup-Assistent ($($Profile.SetupSuffix))..."
    & py -3 -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $EditionDist `
        --workpath (Join-Path $ProjectRoot "build\setup_$($Profile.Key)") `
        $SetupSpec

    if ($LASTEXITCODE -ne 0) {
        throw "Setup-Build fehlgeschlagen fuer $($Profile.SetupSuffix) (Exit-Code $LASTEXITCODE)."
    }

    $BuiltExe = Join-Path $EditionDist "SC_Salvage_Tracker_Setup.exe"
    if (-not (Test-Path $BuiltExe)) {
        throw "Setup-EXE nicht gefunden: $BuiltExe"
    }

    New-Item -ItemType Directory -Force -Path $InstallerOutput | Out-Null
    $SetupExe = Join-Path $InstallerOutput $SetupName
    Copy-Item -Path $BuiltExe -Destination $SetupExe -Force
    Write-Host "Setup-EXE: $SetupExe"

    $ManifestScript = Join-Path $InstallerDir "generate_update_manifest.py"
    $ManifestPath = Join-Path $InstallerOutput ("update-manifest-" + $Profile.Key + ".json")
    & py -3 $ManifestScript `
        --setup $SetupExe `
        --output $ManifestPath `
        --tag "v$AppVersion" `
        --edition $Profile.Key `
        --app-name $Profile.AppName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Update-Manifest: $ManifestPath"
        if ($Profile.Key -eq "solo") {
            $DefaultManifest = Join-Path $InstallerOutput "update-manifest.json"
            Copy-Item -Path $ManifestPath -Destination $DefaultManifest -Force
            Write-Host "Standard-Manifest: $DefaultManifest"
        }
    }

    return $SetupExe
}

function Build-EditionInstaller {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EditionKey,
        [Parameter(Mandatory = $true)]
        [hashtable]$VersionMeta,
        [switch]$SkipPyInstaller,
        [switch]$SkipInno
    )

    if (-not $EditionProfiles.ContainsKey($EditionKey)) {
        throw "Unbekannte Edition: $EditionKey"
    }

    $Profile = $EditionProfiles[$EditionKey]
    $AppOutput = Join-Path $ReleaseRoot ("app\" + $Profile.AppFolder)

    Write-Host ""
    Write-Host "========================================"
    Write-Host " Edition: $($Profile.AppName)"
    Write-Host "========================================"
    Write-Host ""

    if (-not $SkipPyInstaller) {
        Build-AppBundle -Profile $Profile -AppOutput $AppOutput
    }
    else {
        if (-not (Test-Path $AppOutput)) {
            throw "App-Ordner fehlt: $AppOutput (ohne -SkipPyInstaller bauen)"
        }
        Write-Host "PyInstaller uebersprungen: $AppOutput"
    }

    if ($SkipInno) {
        return $null
    }

    if ($UseInno) {
        return Build-InnoSetup -Profile $Profile -AppOutput $AppOutput -VersionMeta $VersionMeta
    }

    return Build-PySideSetup -Profile $Profile -AppOutput $AppOutput -VersionMeta $VersionMeta
}

$VersionMeta = Get-VersionMeta (Join-Path $ProjectRoot "config\version.py")

Write-Host "Projekt:   $ProjectRoot"
Write-Host "Release:   $ReleaseRoot"
Write-Host "Edition:   $Edition"
Write-Host "Version:   $($VersionMeta.DisplayVersion) (Build $($VersionMeta.Build) - $($VersionMeta.Codename))"
Write-Host ""

Set-Location $ProjectRoot

Write-Host "Installer-Grafiken vorbereiten..."
& (Join-Path $InstallerDir "prepare_installer_assets.ps1")

$EditionKeys = if ($Edition -eq "all") {
    @("solo", "crew", "orga")
}
else {
    @($Edition)
}

$BuiltSetups = @()
foreach ($EditionKey in $EditionKeys) {
    $setup = Build-EditionInstaller `
        -EditionKey $EditionKey `
        -VersionMeta $VersionMeta `
        -SkipPyInstaller:$SkipPyInstaller `
        -SkipInno:$SkipInno
    if ($setup) {
        $BuiltSetups += $setup
    }
}

Set-BuildEditionMarker -EditionKey "solo"

Write-Host ""
Write-Host "Fertig!"
if ($BuiltSetups.Count -gt 0) {
    Write-Host "Erstellte Setups:"
    foreach ($setup in $BuiltSetups) {
        Write-Host "  - $setup"
    }
}
Write-Host ""
Write-Host "Hinweis: SOLO-Manifest fuer In-App-Updates als update-manifest.json"
Write-Host "         auf GitHub benennen (oder SOLO-Build als Standard-Release)."
