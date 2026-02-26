# ─────────────────────────────────────────────────────────────────────────────
# LeoSetter — One-command build script
# Usage:  .\build.ps1
#
# Requires:
#   • Python 3.10+ with the project venv active  (or this script activates it)
#   • PyInstaller  (pip install pyinstaller)
#   • Inno Setup 6.x  installed to the default location
#     https://jrsoftware.org/isdl.php
# ─────────────────────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"

# ── Paths ────────────────────────────────────────────────────────────────────
$Root      = $PSScriptRoot
$VenvPy    = Join-Path $Root ".venv\Scripts\python.exe"
$Spec      = Join-Path $Root "leosetter.spec"
$InnoISS   = Join-Path $Root "installer.iss"
$IsccPath  = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# ── Step 1 — Activate virtual environment ───────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " LeoSetter Build Script" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

if (Test-Path $VenvPy) {
    Write-Host "[1/3] Using virtual environment: $VenvPy" -ForegroundColor Green
    $Py = $VenvPy
} else {
    Write-Host "[1/3] Virtual environment not found — using system Python" -ForegroundColor Yellow
    $Py = "python"
}

# ── Step 2 — PyInstaller: build the onefile EXE ─────────────────────────────
Write-Host ""
Write-Host "[2/3] Running PyInstaller..." -ForegroundColor Cyan

Push-Location $Root
try {
    & $Py -m PyInstaller $Spec --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

Write-Host "      EXE built → dist\LeoSetter.exe" -ForegroundColor Green

# ── Step 3 — Inno Setup: build the installer ────────────────────────────────
Write-Host ""
Write-Host "[3/3] Running Inno Setup..." -ForegroundColor Cyan

if (-not (Test-Path $IsccPath)) {
    Write-Host ""
    Write-Host "ERROR: Inno Setup not found at:" -ForegroundColor Red
    Write-Host "       $IsccPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Download and install Inno Setup 6 from:" -ForegroundColor Yellow
    Write-Host "  https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    exit 1
}

& $IsccPath $InnoISS
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE" }

# ── Done ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════════" -ForegroundColor Green
Write-Host " Build complete!" -ForegroundColor Green
Write-Host "══════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host " Installer → installer_output\LeoSetterSetup.exe" -ForegroundColor White
Write-Host ""
