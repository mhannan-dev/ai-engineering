"""Home and root health check endpoints."""

from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from knowledge_worker.api.deps import SettingsDep

router = APIRouter()


@router.get("/", summary="Root", tags=["home"])
@router.get("/health", summary="Health check", tags=["health"])
def read_root(request: Request, settings: SettingsDep) -> Response:
    """Root and health endpoint returning welcome message, status, and API metadata."""
    payload: dict[str, Any] = {
        "title": settings.PROJECT_NAME,
        "meta_title": settings.PROJECT_NAME,
        "status": "ok",
        "message": "Welcome to my FastAPI application!",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }

    # If viewed in a web browser, return a rich HTML landing page with proper meta title tags
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not accept.startswith("*/*"):
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{settings.PROJECT_NAME}</title>
    <meta name="title" content="{settings.PROJECT_NAME}">
    <meta name="description" content="Hybrid-search RAG over English and Bangla documents.">
    <style>
        :root {{
            --bg: #0b0f19;
            --card-bg: rgba(17, 24, 39, 0.85);
            --border: rgba(255, 255, 255, 0.1);
            --primary: #38bdf8;
            --text: #f3f4f6;
            --text-muted: #9ca3af;
            --success: #34d399;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        body {{
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 2.5rem;
            max-width: 580px;
            width: 100%;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(12px);
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(52, 211, 153, 0.15);
            color: var(--success);
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 1.25rem;
        }}
        .dot {{ width: 8px; height: 8px; background: var(--success); border-radius: 50%; }}
        h1 {{ font-size: 1.75rem; font-weight: 700; color: #fff; margin-bottom: 0.75rem; }}
        p {{ color: var(--text-muted); line-height: 1.6; margin-bottom: 1.5rem; }}
        .actions {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
        .btn {{
            display: inline-flex;
            align-items: center;
            padding: 0.75rem 1.25rem;
            border-radius: 0.5rem;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.95rem;
            transition: all 0.2s;
        }}
        .btn-primary {{ background: var(--primary); color: #0b0f19; }}
        .btn-primary:hover {{ opacity: 0.9; }}
        .btn-secondary {{ background: rgba(255, 255, 255, 0.05); color: #fff; border: 1px solid var(--border); }}
        .btn-secondary:hover {{ background: rgba(255, 255, 255, 0.1); }}
        .meta-footer {{ margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border); font-size: 0.8rem; color: var(--text-muted); display: flex; justify-content: space-between; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="badge"><span class="dot"></span> System Status: Online (ok)</div>
        <h1>{settings.PROJECT_NAME}</h1>
        <p>{payload["message"]} High-performance multilingual enterprise RAG engine supporting English and Bangla document intelligence.</p>
        <div class="actions">
            <a href="/docs" class="btn btn-primary">Interactive Swagger Docs</a>
            <a href="/redoc" class="btn btn-secondary">ReDoc API Specs</a>
        </div>
        <div class="meta-footer">
            <span>Version {settings.VERSION}</span>
            <span>API v1: {settings.API_V1_STR}</span>
        </div>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html_content)

    return JSONResponse(content=payload)
