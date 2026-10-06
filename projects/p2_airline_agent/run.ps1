<#
.SYNOPSIS
    One-click runner and management script for Project 2: Multi-Modal Airline Customer Support Agent.

.DESCRIPTION
    Runs the Streamlit interactive UI (Bilingual Agent with Boarding Pass Vision & Clean Architecture).

.PARAMETER Test
    Runs the automated pytest test suite with test coverage reporting.

.PARAMETER Install
    Installs project dependencies from requirements.txt.

.PARAMETER Stop
    Stops any running instances on Streamlit default port 8501.

.EXAMPLE
    .\run.ps1
    # Launches the Streamlit Airline Agent in your browser.

.EXAMPLE
    .\run.ps1 -Test
    # Runs the 14 unit and integration tests.

.EXAMPLE
    .\run.ps1 -Stop
    # Terminates any active servers on port 8501.
#>

[CmdletBinding()]
param (
    [switch]$Test,
    [switch]$Install,
    [switch]$Stop
)

$ProjectRoot = $PSScriptRoot
$RootVenv = Join-Path (Split-Path (Split-Path $ProjectRoot -Parent) -Parent) ".venv"

function Print-Banner {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "   [P2] Multi-Modal Airline Customer Support Agent ✈️     " -ForegroundColor Yellow
    Write-Host "   Clean Architecture Streamlit Application               " -ForegroundColor DarkGray
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Stop-PortProcesses {
    param([int[]]$Ports)
    foreach ($p in $Ports) {
        $conns = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
        if ($conns) {
            foreach ($conn in $conns) {
                if ($conn.OwningProcess -and $conn.OwningProcess -ne 0) {
                    Write-Host "[*] Stopping existing process on port $p (PID: $($conn.OwningProcess))..." -ForegroundColor DarkYellow
                    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }
}

Print-Banner

# 1. Stop Mode
if ($Stop) {
    Write-Host "[*] Cleaning up port 8501..." -ForegroundColor Yellow
    Stop-PortProcesses @(8501)
    Write-Host "[OK] Stopped active Streamlit servers." -ForegroundColor Green
    return
}

# Use active/default python interpreter
$PythonCmd = "python"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    # Check if uv is available for fast running
}

# 2. Install Dependencies
if ($Install) {
    Write-Host "[*] Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    & $PythonCmd -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
    Write-Host "[OK] Dependencies installed." -ForegroundColor Green
    return
}

# 3. Test Mode
if ($Test) {
    Write-Host "[*] Running Pytest Test Suite..." -ForegroundColor Yellow
    Push-Location $ProjectRoot
    try {
        & $PythonCmd -m pytest
    } finally {
        Pop-Location
    }
    return
}

# 4. Default Mode: Launch Streamlit App
Write-Host "[*] Launching Airline Customer Support Agent at http://localhost:8501..." -ForegroundColor Green
Write-Host "  - UI:       Streamlit Interactive Chat & Vision Parsing" -ForegroundColor Cyan
Write-Host "  - Sample:   fixtures/sample_boarding_pass.png" -ForegroundColor DarkCyan
Write-Host "  - Stop:     Press Ctrl+C to stop" -ForegroundColor DarkGray
Write-Host ""

# Ensure port 8501 is not locked
Stop-PortProcesses @(8501)

# Set PYTHONPATH to include src directory
$env:PYTHONPATH = "$ProjectRoot\src;$ProjectRoot"

Push-Location $ProjectRoot
try {
    & $PythonCmd -m streamlit run src/airline_agent/ui/app.py
} finally {
    Pop-Location
    Write-Host "`n[OK] Streamlit application stopped." -ForegroundColor Green
}
