<#
.SYNOPSIS
    Runner for Project 5: Enterprise Knowledge Worker (hybrid-search RAG, English + Bangla).

.PARAMETER Install
    Syncs Python dependencies (uv), applies migrations and downloads the embedding model (~2.2 GB).

.PARAMETER Migrate
    Applies pending database migrations (alembic upgrade head).

.PARAMETER Test
    Runs the backend test suite (pytest).

.PARAMETER Eval
    Runs the Phase 5 Information Retrieval ablation benchmark over the golden dataset.

.PARAMETER Qdrant
    Starts the optional Qdrant server (docker compose). Set QDRANT_URL in api/.env to use it.

.PARAMETER Web
    Starts the Next.js frontend web workspace (npm run dev).

.PARAMETER Stop
    Stops the API on port 8000.

.EXAMPLE
    .\run.ps1 -Install
    .\run.ps1            # API at http://localhost:8000 + Web UI at http://localhost:3000
    .\run.ps1 -Web       # Next.js only (if API is already running separately)
#>

[CmdletBinding()]
param (
    [switch]$Install,
    [switch]$Migrate,
    [switch]$Test,
    [switch]$Eval,
    [switch]$Web,
    [switch]$Qdrant,
    [switch]$Stop
)

$ProjectRoot = $PSScriptRoot
$ApiDir = Join-Path $ProjectRoot "api"
# A globally activated venv (e.g. the repo root .venv) would make uv warn and ignore it anyway
Remove-Item Env:VIRTUAL_ENV -ErrorAction SilentlyContinue
$env:PYTHONUTF8 = "1"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   [P5] Enterprise Knowledge Worker (Hybrid RAG, EN + BN)  " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

function Invoke-InApi([scriptblock]$Block) {
    Push-Location $ApiDir
    try { & $Block } finally { Pop-Location }
}

if ($Stop) {
    foreach ($port in @(8000, 3000)) {
        $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        foreach ($conn in $conns) {
            if ($conn.OwningProcess) {
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
    }
    Write-Host "[OK] Ports 8000 and 3000 are free." -ForegroundColor Green
    return
}

if ($Install) {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] 'uv' not found. Install it from https://astral.sh/uv" -ForegroundColor Red
        return
    }
    Invoke-InApi {
        Write-Host "[1/3] Syncing dependencies..." -ForegroundColor Cyan
        & uv sync
        if ($LASTEXITCODE -ne 0) { throw "uv sync failed" }
        Write-Host "[2/3] Applying migrations..." -ForegroundColor Cyan
        & uv run alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw "alembic upgrade failed" }
        Write-Host "[3/3] Downloading embedding model (first time ~2.2 GB)..." -ForegroundColor Cyan
        & uv run python -c "import sys; sys.path.insert(0, 'src'); from knowledge_worker.services.container import Container; from knowledge_worker.config import get_settings; c = Container(get_settings()); print('dim', len(c.embedder.embed_query('ok'))); c.shutdown()"
        if ($LASTEXITCODE -ne 0) { throw "model download failed" }
    }
    Write-Host "[DONE] Ready. Start the API with .\run.ps1" -ForegroundColor Green
    return
}

if ($Migrate) {
    Invoke-InApi { & uv run alembic upgrade head }
    return
}

if ($Test) {
    Invoke-InApi { & uv run pytest }
    return
}

if ($Eval) {
    Invoke-InApi { & uv run python -m knowledge_worker.evaluation.cli }
    return
}

if ($Web) {
    Push-Location (Join-Path $ProjectRoot "web")
    try {
        Write-Host "[*] Starting Next.js Web UI on http://localhost:3000..." -ForegroundColor Cyan
        & npm run dev
    } finally {
        Pop-Location
    }
    return
}

if ($Qdrant) {
    Push-Location $ProjectRoot
    try { & docker compose up -d } finally { Pop-Location }
    Write-Host "[OK] Qdrant at http://localhost:6333 (dashboard: /dashboard)." -ForegroundColor Green
    Write-Host "     Set QDRANT_URL=http://localhost:6333 in api/.env and re-index documents." -ForegroundColor DarkGray
    return
}

foreach ($portEntry in @(@{Port=8000; Name="API"}, @{Port=3000; Name="Web"})) {
    $existing = Get-NetTCPConnection -LocalPort $portEntry.Port -State Listen -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "[!] Port $($portEntry.Port) ($($portEntry.Name)) already in use. Stopping..." -ForegroundColor Yellow
        foreach ($conn in $existing) {
            if ($conn.OwningProcess) {
                Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            }
        }
    }
}
Start-Sleep -Milliseconds 500

Write-Host "[*] API:     http://localhost:8000  (Swagger: /docs)" -ForegroundColor Cyan
Write-Host "[*] Web UI:  http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

# Start Next.js web UI in a background job
$WebDir = Join-Path $ProjectRoot "web"
$webJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    & npm run dev
} -ArgumentList $WebDir

Write-Host "[+] Next.js starting in background (job $($webJob.Id))..." -ForegroundColor DarkGray
Write-Host "    Press Ctrl+C to stop both services." -ForegroundColor DarkGray
Write-Host ""

try {
    # Run the API in the foreground
    Invoke-InApi { & uv run fastapi dev main.py }
} finally {
    Write-Host "" -ForegroundColor Gray
    Write-Host "[*] Stopping Next.js web job..." -ForegroundColor Yellow
    Stop-Job  -Job $webJob -ErrorAction SilentlyContinue
    Remove-Job -Job $webJob -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] All services stopped." -ForegroundColor Green
}
