<#
Build the Snapshot Decoder Windows installer.

Run this from a build-only clone on the Windows machine, e.g.:

    git clone https://github.com/nathanladd/Snapshot-Decoder C:\src\Snapshot-Decoder
    cd C:\src\Snapshot-Decoder
    powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
    powershell -ExecutionPolicy Bypass -File .\build_windows.ps1 -Branch some-branch

Steps: sync the clone to origin/<Branch>, create the venv and install
requirements_build.txt (again only when that file changes), run build_exe.py,
compile create_installer.iss with Inno Setup, and copy the installer to
the shared folder (-OutputDir) as SnapshotDecoder_Setup_<version>.exe.

The sync DISCARDS local changes in this clone (build_exe.py rewrites
create_installer.iss on every run), so don't edit code in the build clone.

One-time setup:
    winget install Git.Git Python.Python.3.12 JRSoftware.InnoSetup
#>

param(
    [string]$Branch = "main",
    # The Omarchy Windows VM's shared folder (~/Windows on the Linux side).
    [string]$OutputDir = "\\host.lan\Data",
    [string]$PythonVersion = "3.12",
    [switch]$NoSync
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Invoke-Native {
    # Windows PowerShell doesn't stop on a native command's exit code; check it here.
    param([string]$File, [string[]]$Arguments)
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "'$File $($Arguments -join ' ')' failed with exit code $LASTEXITCODE"
    }
}

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

# ---- Sync to the requested branch ----
if (-not $NoSync) {
    Write-Step "Syncing to origin/$Branch"
    Invoke-Native git @("fetch", "--prune", "origin")
    Invoke-Native git @("checkout", "--force", "-B", $Branch, "origin/$Branch")
    Invoke-Native git @("clean", "-fdq")
}
$commit = (git rev-parse --short HEAD).Trim()

# ---- Python environment ----
$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Step "Creating venv with Python $PythonVersion"
    Invoke-Native py @("-$PythonVersion", "-m", "venv", "venv")
}

$requirements = Join-Path $PSScriptRoot "requirements_build.txt"
$stamp = Join-Path $PSScriptRoot "venv\requirements_build.sha256"
$hash = (Get-FileHash $requirements -Algorithm SHA256).Hash
if (-not (Test-Path $stamp) -or (Get-Content $stamp -Raw).Trim() -ne $hash) {
    Write-Step "Installing build requirements"
    Invoke-Native $venvPython @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-Native $venvPython @("-m", "pip", "install", "-r", $requirements)
    Set-Content -Path $stamp -Value $hash
}

# ---- PyInstaller ----
Write-Step "Building executable ($commit)"
Invoke-Native $venvPython @("build_exe.py")

# ---- Inno Setup ----
$iscc = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source,
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $iscc) {
    throw "Inno Setup not found. Install it with: winget install JRSoftware.InnoSetup"
}

Write-Step "Compiling installer"
Invoke-Native $iscc @("/Qp", "create_installer.iss")

# ---- Copy to the shared folder ----
$version = (Select-String -Path "version.py" -Pattern 'APP_VERSION\s*=\s*["'']([^"'']+)["'']').Matches[0].Groups[1].Value
$installer = Join-Path $PSScriptRoot "SnapshotDecoder_Setup.exe"
$target = Join-Path $OutputDir "SnapshotDecoder_Setup_$version.exe"

if (Test-Path $OutputDir) {
    Copy-Item $installer $target -Force
    Write-Step "Done: $target (version $version, commit $commit)"
} else {
    Write-Warning "Shared folder $OutputDir not reachable; installer left at $installer"
    Write-Step "Done: $installer (version $version, commit $commit)"
}
