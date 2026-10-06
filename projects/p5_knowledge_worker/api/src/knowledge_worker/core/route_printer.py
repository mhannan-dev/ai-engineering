"""Terminal route printer for local development."""

import os
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI

# ANSI Color codes for terminal styling
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_BOLD_CYAN = "\033[1;36m"
_BOLD_WHITE = "\033[1;37m"
_GRAY = "\033[90m"

_METHOD_COLORS: dict[str, str] = {
    "GET": "\033[1;32m",     # Bold Green
    "POST": "\033[1;34m",    # Bold Blue
    "PUT": "\033[1;33m",     # Bold Yellow
    "PATCH": "\033[1;35m",   # Bold Magenta
    "DELETE": "\033[1;31m",  # Bold Red
    "HEAD": "\033[2;37m",    # Dim White
    "OPTIONS": "\033[2;37m", # Dim White
}


def _supports_color() -> bool:
    """Check if the current terminal environment supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def format_routes(app: "FastAPI") -> list[dict[str, Any]]:
    """Extract and sort all API routes from the FastAPI application schema."""
    openapi = app.openapi()
    paths = openapi.get("paths", {})
    routes: list[dict[str, Any]] = []

    method_order = {"GET": 1, "POST": 2, "PUT": 3, "PATCH": 4, "DELETE": 5}

    for path, path_item in sorted(paths.items()):
        for method, details in path_item.items():
            method_upper = method.upper()
            if method_upper in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
                summary = details.get("summary") or details.get("description") or ""
                # Keep summary single line for table display
                if "\n" in summary:
                    summary = summary.split("\n")[0]
                tags = details.get("tags") or []
                routes.append({
                    "method": method_upper,
                    "path": path,
                    "summary": summary,
                    "tags": tags,
                    "order": method_order.get(method_upper, 99),
                })

    # Sort primarily by path, then by HTTP method order
    routes.sort(key=lambda r: (r["path"], r["order"]))
    return routes


def print_api_routes(app: "FastAPI", base_url: str = "http://localhost:8000") -> None:
    """Print a clean, formatted table of all registered API routes in the terminal."""
    use_color = _supports_color()

    def c(code: str, text: str) -> str:
        return f"{code}{text}{_RESET}" if use_color else text

    try:
        routes = format_routes(app)
    except Exception:
        return

    if not routes:
        return

    # Calculate column widths
    max_method_len = max((len(r["method"]) for r in routes), default=6)
    max_method_len = max(max_method_len, len("Method"))

    max_path_len = max((len(r["path"]) for r in routes), default=20)
    max_path_len = max(max_path_len, len("Endpoint"))

    max_tag_len = max((len(r["tags"][0]) if r["tags"] else 0 for r in routes), default=4)
    max_tag_len = max(max_tag_len, len("Tag"))

    line_width = max(max_method_len + max_path_len + max_tag_len + 35, 78)

    divider = "-" * line_width
    border_top = "=" * line_width

    output_lines: list[str] = [
        "",
        c(_BOLD_CYAN, f"[{border_top}]"),
        c(_BOLD_CYAN, f"  {app.title} ({app.version}) - Registered API Routes"),
        c(_DIM, f"  Swagger: {base_url}/docs  |  ReDoc: {base_url}/redoc  |  OpenAPI: {base_url}/openapi.json"),
        c(_BOLD_CYAN, f"[{border_top}]"),
        f"  {c(_BOLD_WHITE, 'Method'.ljust(max_method_len))}  {c(_BOLD_WHITE, 'Endpoint'.ljust(max_path_len))}  {c(_BOLD_WHITE, 'Tag'.ljust(max_tag_len + 2))}  {c(_BOLD_WHITE, 'Summary')}",
        c(_GRAY, f"  {divider}"),
    ]

    for r in routes:
        method = r["method"]
        method_color = _METHOD_COLORS.get(method, _BOLD_WHITE)
        method_str = c(method_color, method.ljust(max_method_len))
        path_str = c(_BOLD_WHITE, r["path"].ljust(max_path_len))
        tag_name = r["tags"][0] if r["tags"] else "-"
        tag_str = c(_CYAN, f"[{tag_name}]".ljust(max_tag_len + 2))
        summary_str = c(_GRAY, r["summary"])

        output_lines.append(f"  {method_str}  {path_str}  {tag_str}  {summary_str}")

    output_lines.append(c(_GRAY, f"  {divider}"))
    output_lines.append(c(_DIM, f"  Total: {len(routes)} registered endpoints (Local Dev Mode)"))
    output_lines.append("")

    content = "\n".join(output_lines)
    try:
        print(content, flush=True)
    except UnicodeEncodeError:
        # Fallback to ascii replacement in case terminal charset is restricted
        print(content.encode("ascii", errors="replace").decode("ascii"), flush=True)
