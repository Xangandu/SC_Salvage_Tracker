# Vollautomatischer Release - ohne Rueckfragen
# Wird von Release_veroeffentlichen.bat und der Cursor-Task aufgerufen.
#
# Einmalig vorher: gh auth login
# Optional PATCHNOTES: config/patchnotes_ai.local.json
# Vor neuem Release: APP_VERSION in config/version.py erhoehen

$ErrorActionPreference = "Stop"

$InstallerDir = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $InstallerDir
$VersionFile = Join-Path $ProjectRoot "config\version.py"
$PatchnotesFile = Join-Path $ProjectRoot "Changelogs\PATCHNOTES.txt"
$PublishScript = Join-Path $InstallerDir "publish_release.ps1"

$VersionHeadingPattern = '(?ms)^VERSION \d'
$EqualsDividerPattern = '={3,}\r?\n'

function Get-VersionMeta {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Nicht gefunden: $Path - bitte config/version.py pflegen."
    }

    $content = Get-Content $Path -Raw
    $meta = @{
        FileVersion = ""
        DisplayVersion = ""
        Build = ""
        Codename = ""
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

    if (-not $meta.FileVersion) {
        throw "APP_VERSION in config/version.py ist leer oder ungueltig."
    }

    return $meta
}

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host ">> $Message"
}

function Get-PythonExecutable {
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }
    return "py"
}

function Invoke-AiPatchnotes {
    param([hashtable]$VersionMeta)

    $python = Get-PythonExecutable
    $script = Join-Path $ProjectRoot "scripts\generate_patchnotes_ai.py"

    if (-not (Test-Path $script)) {
        Write-Host "   Hinweis - KI-Skript fehlt, Fallback aktiv"
        return $false
    }

    $hasKey = [bool]$env:OPENAI_API_KEY
    $localConfig = Join-Path $ProjectRoot "config\patchnotes_ai.local.json"
    if (-not $hasKey -and -not (Test-Path $localConfig)) {
        Write-Host "   Hinweis - kein API-Key, Fallback auf Platzhalter"
        return $false
    }

    Write-Host "   ChatGPT schreibt PATCHNOTES fuer $($VersionMeta.DisplayVersion)..."

    if ($python -eq "py") {
        & py -3 $script
    }
    else {
        & $python $script
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "   OK - PATCHNOTES per ChatGPT erstellt"
        return $true
    }

    if ($LASTEXITCODE -eq 2) {
        Write-Host "   Fallback - Platzhalter-Text wird verwendet"
        return $false
    }

    Write-Warning "   ChatGPT fehlgeschlagen - Fallback auf Platzhalter"
    return $false
}

function Ensure-PatchnotesSection {
    param(
        [string]$Path,
        [hashtable]$VersionMeta
    )

    if (-not (Test-Path $Path)) {
        $header = @"
SC SALVAGE TRACKER - PATCHNOTES
================================

"@
        Set-Content -Path $Path -Value $header -Encoding utf8
    }

    $content = Get-Content $Path -Raw
    $versionToken = $VersionMeta.DisplayVersion

    if ($content -match [regex]::Escape($versionToken)) {
        Write-Host "   OK - PATCHNOTES enthaelt $versionToken"
        return
    }

    $divider = ("-" * 68)
    $block = @"
VERSION $($VersionMeta.DisplayVersion) | Build $($VersionMeta.Build) | Codename: $($VersionMeta.Codename)
$divider

- Release $($VersionMeta.DisplayVersion) - Details bitte bei Bedarf ergaenzen
- Siehe Git-Commit-Historie fuer technische Aenderungen


"@

    if ($content -match $VersionHeadingPattern) {
        $match = [regex]::Match($content, $VersionHeadingPattern)
        $newContent = (
            $content.Substring(0, $match.Index) +
            $block +
            $content.Substring($match.Index)
        )
    }
    elseif ($content -match $EqualsDividerPattern) {
        $newContent = $content -replace $EqualsDividerPattern, ('$0' + "`n$block")
    }
    else {
        $newContent = $block + $content
    }

    Set-Content -Path $Path -Value ($newContent.TrimEnd() + "`n") -Encoding utf8
    Write-Host "   OK - PATCHNOTES-Eintrag fuer $versionToken automatisch ergaenzt"
}

Set-Location $ProjectRoot

Write-Host ""
Write-Host "========================================================"
Write-Host " SC Salvage Tracker - Vollautomatischer Release"
Write-Host "========================================================"

Write-Step "Schritt 1/5 - Version lesen"
$version = Get-VersionMeta $VersionFile
Write-Host "   Version:  $($version.DisplayVersion)"
Write-Host "   Build:    $($version.Build)"
Write-Host "   Codename: $($version.Codename)"
Write-Host "   Git-Tag:  v$($version.FileVersion)"

Write-Step "Schritt 2/5 - PATCHNOTES (ChatGPT)"
$aiPatchnotesOk = Invoke-AiPatchnotes -VersionMeta $version
if (-not $aiPatchnotesOk) {
    Ensure-PatchnotesSection -Path $PatchnotesFile -VersionMeta $version
}

Write-Step "Schritt 3/5 - Voraussetzungen"
if (-not (Test-CommandExists "git")) {
    throw "Git nicht gefunden - bitte Git installieren."
}
Write-Host "   OK - git"

if (-not (Test-CommandExists "gh")) {
    throw "GitHub CLI (gh) nicht gefunden. Installation: https://cli.github.com/ - danach: gh auth login"
}
gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "gh nicht angemeldet - bitte einmalig ausfuehren: gh auth login"
}
Write-Host "   OK - gh (angemeldet)"

if (-not (Test-CommandExists "py")) {
    throw "Python (py) nicht gefunden."
}
Write-Host "   OK - Python"

$commitMessage = "Release $($version.DisplayVersion)"

Write-Step "Schritt 4/5 - Build, Commit, Push"
Write-Host "   Commit-Nachricht: $commitMessage"

& powershell -NoProfile -ExecutionPolicy Bypass -File $PublishScript `
    -CommitMessage $commitMessage

if ($LASTEXITCODE -ne 0) {
    throw "Release fehlgeschlagen (Exit-Code $LASTEXITCODE)."
}

Write-Step "Schritt 5/5 - Fertig"
Write-Host ""
Write-Host "========================================================"
Write-Host " Release $($version.DisplayVersion) erfolgreich veroeffentlicht"
Write-Host "========================================================"
Write-Host ""
