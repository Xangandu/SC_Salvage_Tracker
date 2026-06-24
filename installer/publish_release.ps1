# SC Salvage Tracker - Build + GitHub Release in einem Schritt
#
# Standard:
#   powershell -ExecutionPolicy Bypass -File installer\publish_release.ps1
#
# Mit Commit + Push:
#   powershell -ExecutionPolicy Bypass -File installer\publish_release.ps1 `
#     -CommitMessage "Release 0.16.0 Beta"

param(
    [ValidateSet("solo", "crew", "orga", "all")]
    [string]$Edition = "solo",
    [switch]$SkipBuild,
    [switch]$Draft,
    [switch]$ReplaceRelease,
    [string]$CommitMessage = "",
    [string]$NotesFile = "",
    [string]$Tag = ""
)

$ErrorActionPreference = "Stop"

$InstallerDir = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $InstallerDir
$ScRoot = Split-Path -Parent (Split-Path -Parent $ProjectRoot)
$ReleaseRoot = Join-Path $ScRoot "Release"
$InstallerOutput = Join-Path $ReleaseRoot "installer"
$VersionFile = Join-Path $ProjectRoot "config\version.py"
$BuildScript = Join-Path $InstallerDir "build_installer.ps1"

$EditionSuffix = @{
    solo = "SOLO"
    crew = "CREW"
    orga = "ORGA"
}

function Get-VersionMeta {
    param([string]$Path)
    $content = Get-Content $Path -Raw
    $meta = @{
        FileVersion = "0.0.0"
        DisplayVersion = "0.0.0"
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

    return $meta
}

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Assert-GhReady {
    if (-not (Test-CommandExists "gh")) {
        throw "GitHub CLI (gh) nicht gefunden. Installation: https://cli.github.com/ - danach: gh auth login"
    }

    gh auth status 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "gh ist nicht angemeldet. Bitte ausfuehren: gh auth login"
    }
}

function Get-EditionKeys {
    param([string]$EditionChoice)
    if ($EditionChoice -eq "all") {
        return @("solo", "crew", "orga")
    }
    return @($EditionChoice)
}

function Get-ReleaseAssetPaths {
    param(
        [string[]]$EditionKeys,
        [string]$FileVersion,
        [string]$OutputDir
    )

    $assets = @()
    $seen = @{}

    foreach ($editionKey in $EditionKeys) {
        $suffix = $EditionSuffix[$editionKey]
        $setupName = "SC_Salvage_Tracker_Setup_${suffix}_$FileVersion.exe"
        $setupPath = Join-Path $OutputDir $setupName

        if (-not (Test-Path $setupPath)) {
            throw "Setup fehlt: $setupPath - zuerst bauen (ohne -SkipBuild) oder Edition pruefen."
        }

        if (-not $seen.ContainsKey($setupPath)) {
            $assets += $setupPath
            $seen[$setupPath] = $true
        }

        if ($editionKey -eq "solo") {
            $manifestPath = Join-Path $OutputDir "update-manifest.json"
        }
        else {
            $manifestPath = Join-Path $OutputDir ("update-manifest-$editionKey.json")
        }

        if (-not (Test-Path $manifestPath)) {
            throw "Update-Manifest fehlt: $manifestPath"
        }

        if (-not $seen.ContainsKey($manifestPath)) {
            $assets += $manifestPath
            $seen[$manifestPath] = $true
        }
    }

    return $assets
}

function Invoke-GitCommitAndPush {
    param(
        [string]$Message,
        [string]$WorkingDirectory
    )

    if (-not (Test-CommandExists "git")) {
        throw "Git nicht gefunden - CommitMessage kann nicht ausgefuehrt werden."
    }

    Push-Location $WorkingDirectory
    try {
        $status = git status --porcelain
        if (-not $status) {
            Write-Host "Git: Keine Aenderungen zum Committen."
        }
        else {
            Write-Host "Git: Commit erstellen..."
            git add -A
            git commit -m $Message
            if ($LASTEXITCODE -ne 0) {
                throw "git commit fehlgeschlagen."
            }
        }

        Write-Host "Git: Push..."
        git push origin HEAD
        if ($LASTEXITCODE -ne 0) {
            throw "git push fehlgeschlagen."
        }
    }
    finally {
        Pop-Location
    }
}

function Remove-ExistingRelease {
    param([string]$ReleaseTag)

    gh release view $ReleaseTag --json id 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Vorhandenes Release $ReleaseTag wird ersetzt..."
        gh release delete $ReleaseTag --yes
        if ($LASTEXITCODE -ne 0) {
            throw "gh release delete fehlgeschlagen."
        }
    }

    $localTag = git tag -l $ReleaseTag 2>$null
    if ($localTag) {
        git tag -d $ReleaseTag | Out-Null
    }

    git push origin --delete $ReleaseTag 2>$null | Out-Null
}

$VersionMeta = Get-VersionMeta $VersionFile
$ReleaseTag = if ($Tag) {
    if ($Tag -notmatch '^v') { "v$Tag" } else { $Tag }
}
else {
    "v$($VersionMeta.FileVersion)"
}

if (-not $NotesFile) {
    $NotesFile = Join-Path $ProjectRoot "Changelogs\PATCHNOTES.txt"
}
if (-not (Test-Path $NotesFile)) {
    throw "Release-Notizen nicht gefunden: $NotesFile"
}

$EditionKeys = Get-EditionKeys -EditionChoice $Edition
$ReleaseTitle = "SC Salvage Tracker $($VersionMeta.DisplayVersion)"

Write-Host ""
Write-Host "========================================"
Write-Host " SC Salvage Tracker - Release"
Write-Host "========================================"
Write-Host "Version:   $($VersionMeta.DisplayVersion)"
Write-Host "Tag:       $ReleaseTag"
Write-Host "Edition:   $Edition"
Write-Host "Build:     $(-not $SkipBuild)"
Write-Host "Draft:     $Draft"
Write-Host ""

Assert-GhReady

if ($CommitMessage) {
    Invoke-GitCommitAndPush -Message $CommitMessage -WorkingDirectory $ProjectRoot
}

if (-not $SkipBuild) {
    Write-Host "Installer bauen..."
    & powershell -ExecutionPolicy Bypass -File $BuildScript -Edition $Edition
    if ($LASTEXITCODE -ne 0) {
        throw "build_installer.ps1 fehlgeschlagen (Exit-Code $LASTEXITCODE)."
    }
}

$Assets = Get-ReleaseAssetPaths `
    -EditionKeys $EditionKeys `
    -FileVersion $VersionMeta.FileVersion `
    -OutputDir $InstallerOutput

Write-Host ""
Write-Host "Release-Assets:"
foreach ($asset in $Assets) {
    Write-Host "  - $asset"
}
Write-Host ""

$tagExists = $false
$releaseExists = $false

if (Test-CommandExists "git") {
    Push-Location $ProjectRoot
    try {
        $tagExists = [bool](git tag -l $ReleaseTag)
    }
    finally {
        Pop-Location
    }
}

gh release view $ReleaseTag 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    $releaseExists = $true
}

if ($tagExists -or $releaseExists) {
    if (-not $ReplaceRelease) {
        throw (
            "Release-Tag '$ReleaseTag' existiert bereits. " +
            "Version in config/version.py erhoehen oder -ReplaceRelease verwenden."
        )
    }
    Remove-ExistingRelease -ReleaseTag $ReleaseTag
}

$ghArgs = @(
    "release", "create", $ReleaseTag,
    "--title", $ReleaseTitle,
    "--notes-file", $NotesFile,
    "--target", "main"
)

if ($Draft) {
    $ghArgs += "--draft"
}

$ghArgs += $Assets

Write-Host "GitHub Release erstellen..."
& gh @ghArgs
if ($LASTEXITCODE -ne 0) {
    throw "gh release create fehlgeschlagen."
}

$viewUrl = gh release view $ReleaseTag --json url -q .url
Write-Host ""
Write-Host "Fertig!"
Write-Host "Release: $viewUrl"
Write-Host ""
Write-Host "In-App-Updates nutzen update-manifest.json vom latest-Release."
if ($Draft) {
    Write-Host "Hinweis: Release ist noch ein Entwurf - im Browser veroeffentlichen."
}
