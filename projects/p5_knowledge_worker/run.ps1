<#
.SYNOPSIS
    Runner for Project 5: Enterprise Knowledge Worker (hybrid-search RAG, English + Bangla).

.PARAMETER Install
    Syncs Python dependencies (uv), applies migrations and downloads the embedding model (~2.2 GB).

.PARAMETER Migrate
    Applies pending database migrations (alembic upgrade head).

.PARAMETER Test
    Runs the backend test suite (pytest).

.PARAMETER Qdrant
    Starts the optional Qdrant server (docker compose). Set QDRANT_URL in api/.env to use it.

.PARAMETER Stop
    Stops the API on port 8000.

.EXAMPLE
    .\run.ps1 -Install
    .\run.ps1            # API at http://localhost:8000 (Swagger: /docs)
#>

[CmdletBinding()]
param (
    [switch]$Install,
    [switch]$Migrate,
    [switch]$Test,
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
    $conns = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
        if ($conn.OwningProcess) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "[OK] Port 8000 is free." -ForegroundColor Green
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

if ($Qdrant) {
    Push-Location $ProjectRoot
    try { & docker compose up -d } finally { Pop-Location }
    Write-Host "[OK] Qdrant at http://localhost:6333 (dashboard: /dashboard)." -ForegroundColor Green
    Write-Host "     Set QDRANT_URL=http://localhost:6333 in api/.env and re-index documents." -ForegroundColor DarkGray
    return
}

$existing = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[!] Port 8000 is already running (PID: $($existing.OwningProcess)). Stopping previous instance..." -ForegroundColor Yellow
    foreach ($conn in $existing) {
        if ($conn.OwningProcess) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
}

Write-Host "[*] API:     http://localhost:8000" -ForegroundColor Cyan
Write-Host "    Swagger: http://localhost:8000/docs" -ForegroundColor DarkCyan
Invoke-InApi { & uv run fastapi dev main.py }
