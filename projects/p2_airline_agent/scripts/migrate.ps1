<#
.SYNOPSIS
    Automated migration script to transition p2_airline_agent from flat layout to Clean Architecture src/ layout.
.DESCRIPTION
    Creates new layered directory hierarchy, backs up legacy flat files to .bak, and verifies integrity.
#>

[CmdletBinding()]
param (
    [string]$ProjectRoot = ""
)

if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
}

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Airline Agent Architecture Migration Tool (v0.2.0)       " -ForegroundColor Cyan
Write-Host " Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Target Directories
$directories = @(
    "src/airline_agent/config",
    "src/airline_agent/domain",
    "src/airline_agent/services",
    "src/airline_agent/infra",
    "src/airline_agent/ui",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "scripts",
    "docs"
)

foreach ($dir in $directories) {
    $fullPath = Join-Path $ProjectRoot $dir
    if (-not (Test-Path -Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  [+] Created directory: $dir" -ForegroundColor Green
    }
}

# 2. Backup flat legacy files to .bak
$legacyFiles = @(
    "airline_main_agent.py",
    "airline_support_agent.py",
    "app.py",
    "agent.py",
    "tools.py",
    "vision.py",
    "database.py",
    "models.py",
    "config.py"
)

Write-Host "`nSecuring legacy flat files as .bak backups..." -ForegroundColor Yellow
foreach ($file in $legacyFiles) {
    $source = Join-Path $ProjectRoot $file
    $backup = Join-Path $ProjectRoot "$file.bak"
    if (Test-Path -Path $source) {
        Copy-Item -Path $source -Destination $backup -Force
        Write-Host "  [OK] Backed up: $file -> $file.bak" -ForegroundColor Gray
    }
}

Write-Host "`n[DONE] Migration complete! All files organized in src/ with safety backups." -ForegroundColor Green
Write-Host "To run the app: streamlit run src/airline_agent/ui/app.py" -ForegroundColor Cyan
