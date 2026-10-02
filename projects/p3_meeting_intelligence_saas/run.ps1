<#
.SYNOPSIS
    One-click single-terminal runner and management script for Project 3: Meeting Intelligence SaaS.

.DESCRIPTION
    Runs both FastAPI backend and Next.js frontend in a SINGLE terminal window without
    opening popup windows. When you press Ctrl+C, both services terminate cleanly.

.PARAMETER Backend
    Runs only the FastAPI backend service in the foreground (http://localhost:8000).

.PARAMETER Web
    Runs only the Next.js frontend web application in the foreground (http://localhost:3000).

.PARAMETER Install
    Installs and syncs both Python (uv) and Node.js (npm) dependencies.

.PARAMETER Migrate
    Applies pending database migrations (alembic upgrade head).

.PARAMETER Test
    Runs the backend automated test suite via pytest.

.PARAMETER Stop
    Stops any running instances on ports 8000 and 3000.

.EXAMPLE
    .\run.ps1
    # Runs full stack in this single terminal (Ctrl+C stops both).

.EXAMPLE
    .\run.ps1 -Backend
    # Runs the FastAPI backend only.

.EXAMPLE
    .\run.ps1 -Web
    # Runs the Next.js frontend only.

.EXAMPLE
    .\run.ps1 -Stop
    # Kills any active servers on ports 8000/3000.
#>

[CmdletBinding()]
param (
    [switch]$Backend,

    [Alias("Frontend")]
    [switch]$Web,

    [switch]$Install,

    [switch]$Migrate,

    [switch]$Test,

    [switch]$Stop
)

$ProjectRoot = $PSScriptRoot
$ApiDir = Join-Path $ProjectRoot "api"
$WebDir = Join-Path $ProjectRoot "web"

function Print-Banner {
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "   [P3] Meeting Intelligence & Minutes Engine SaaS        " -ForegroundColor Yellow
    Write-Host "   Single-Terminal Runner (FastAPI + Next.js)             " -ForegroundColor DarkGray
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
    Write-Host "[*] Cleaning up ports 8000 and 3000..." -ForegroundColor Yellow
    Stop-PortProcesses @(8000, 3000)
    Write-Host "[OK] Cleaned up running servers." -ForegroundColor Green
    return
}

# 2. Dependency Installation Mode
if ($Install) {
    Write-Host "[*] Installing and syncing dependencies..." -ForegroundColor Yellow

    Write-Host "`n[1/2] Syncing Python backend virtual environment (uv)..." -ForegroundColor Cyan
    Push-Location $ApiDir
    try {
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            & uv sync
            Write-Host "[OK] Backend dependencies synced successfully." -ForegroundColor Green
        } else {
            Write-Host "[ERROR] 'uv' package manager not found. Please install uv (https://astral.sh/uv)." -ForegroundColor Red
        }
    } finally {
        Pop-Location
    }

    Write-Host "`n[2/2] Installing Next.js frontend packages (npm)..." -ForegroundColor Cyan
    Push-Location $WebDir
    try {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            & npm install
            Write-Host "[OK] Frontend dependencies installed successfully." -ForegroundColor Green
        } else {
            Write-Host "[ERROR] 'npm' not found. Please ensure Node.js is installed." -ForegroundColor Red
        }
    } finally {
        Pop-Location
    }

    Write-Host "`n[DONE] All dependencies ready!" -ForegroundColor Green
    return
}

# 2b. Database Migration Mode
if ($Migrate) {
    Write-Host "[*] Applying database migrations (alembic upgrade head)..." -ForegroundColor Yellow
    Push-Location $ApiDir
    try {
        & uv run alembic upgrade head
    } finally {
        Pop-Location
    }
    return
}

# 3. Automated Test Mode
if ($Test) {
    Write-Host "[*] Running Backend Test Suite (pytest)..." -ForegroundColor Yellow
    Push-Location $ApiDir
    try {
        & uv run pytest
    } finally {
        Pop-Location
    }
    return
}

# 4. Backend-Only Mode (Runs in current terminal)
if ($Backend) {
    Write-Host "[*] Starting FastAPI Backend at http://localhost:8000..." -ForegroundColor Cyan
    Write-Host "    Swagger Docs: http://localhost:8000/docs" -ForegroundColor DarkCyan
    Push-Location $ApiDir
    try {
        & uv run fastapi dev main.py
    } finally {
        Pop-Location
    }
    return
}

# 5. Web-Only Mode (Runs in current terminal)
if ($Web) {
    Write-Host "[*] Starting Next.js Frontend at http://localhost:3000..." -ForegroundColor Cyan
    Push-Location $WebDir
    try {
        & npm run dev
    } finally {
        Pop-Location
    }
    return
}

# 6. Default Mode: Run Both in THIS SINGLE TERMINAL
Write-Host "[*] Starting full stack in single terminal mode..." -ForegroundColor Green
Write-Host "  - Backend:  http://localhost:8000 (Swagger: http://localhost:8000/docs)" -ForegroundColor Cyan
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  - Stop:     Press Ctrl+C to terminate both servers" -ForegroundColor DarkGray
Write-Host ""

# Ensure ports 8000 and 3000 are not locked from previous sessions
Stop-PortProcesses @(8000)

# Launch Backend as a background process (no new window)
Write-Host "[*] Starting FastAPI backend in background..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "uv" -ArgumentList "run", "fastapi", "dev", "main.py" -WorkingDirectory $ApiDir -NoNewWindow -PassThru

# Wait briefly for FastAPI to initialize
Start-Sleep -Seconds 2

try {
    # Run Frontend directly in the foreground of this terminal
    Write-Host "[*] Starting Next.js frontend in foreground..." -ForegroundColor Green
    Push-Location $WebDir
    & npm run dev
}
finally {
    Write-Host "`n[*] Terminating backend server (PID: $($backendProcess.Id))..." -ForegroundColor Yellow
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    # Double check port 8000 is freed
    Stop-PortProcesses @(8000)
    Pop-Location
    Write-Host "[OK] Stopped all services cleanly." -ForegroundColor Green
}
