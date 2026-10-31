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

function Stop-P5Services {
    # Stops this project's API and web, including orphans. `fastapi dev` runs the app in a
    # multiprocessing worker whose command line does not mention this project, and Windows does
    # not stop children when a parent dies. An orphaned worker keeps serving old code on port
    # 8000 and holds the embedded Qdrant lock on data/qdrant, so every new start fails.
    $all = @(Get-CimInstance Win32_Process)
    $patterns = @("*$ApiDir\.venv\*", "*$(Join-Path $ProjectRoot 'web')\node_modules\*")
    $roots = @($all | Where-Object {
        $cmd = $_.CommandLine
        $cmd -and ($patterns | Where-Object { $cmd -like $_ })
    } | ForEach-Object { $_.ProcessId })

    foreach ($port in @(8000, 3000)) {
        $owners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object { $_.OwningProcess } | Where-Object { $_ } | Sort-Object -Unique
        foreach ($owner in $owners) {
            $roots += $owner
            # The listed owner is often the reloader that already exited; its orphaned
            # children still hold the socket.
            $roots += @($all | Where-Object { $_.ParentProcessId -eq $owner } | ForEach-Object { $_.ProcessId })
        }
    }

    $roots = @($roots | Sort-Object -Unique)
    foreach ($id in $roots) {
        # /T stops the whole tree, so reloader workers are not left behind.
        & taskkill.exe /PID $id /T /F 2>$null | Out-Null
    }
    if ($roots.Count -gt 0) {
        Write-Host "[!] Stopped leftover API/Web processes." -ForegroundColor Yellow
        Start-Sleep -Milliseconds 800  # let Windows release the Qdrant lock files
    }
}

if ($Stop) {
    Stop-P5Services
    Write-Host "[OK] API and Web are stopped." -ForegroundColor Green
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
    # Only the Qdrant service; `docker compose up --build` runs the full stack.
    try { & docker compose up -d qdrant } finally { Pop-Location }
    Write-Host "[OK] Qdrant at http://localhost:6333 (dashboard: /dashboard)." -ForegroundColor Green
    Write-Host "     Set QDRANT_URL=http://localhost:6333 in api/.env and re-index documents." -ForegroundColor DarkGray
    return
}

Stop-P5Services

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
