"""Utility script to display all registered FastAPI routes and docs URLs in console."""

import sys
from pathlib import Path

# Ensure src/ is in sys.path
SRC_DIR = str(Path(__file__).resolve().parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from main import app  # noqa: E402


def print_routes(base_url: str = "http://localhost:8000") -> None:
    """Print all endpoints grouped by method and path along with documentation URLs."""
    openapi_schema = app.openapi()
    paths = openapi_schema.get("paths", {})

    # Combine API routes with documentation routes
    all_routes: list[tuple[str, str, str]] = []

    for path, methods in sorted(paths.items()):
        for method, details in methods.items():
            summary = details.get("summary", details.get("description", ""))
            all_routes.append((method.upper(), path, summary))

    # Add documentation endpoints to table if configured
    if app.docs_url:
        all_routes.append(("GET", app.docs_url, "Interactive Swagger UI documentation"))
    if app.redoc_url:
        all_routes.append(("GET", app.redoc_url, "ReDoc visual API documentation"))
    if app.openapi_url:
        all_routes.append(("GET", app.openapi_url, "Raw OpenAPI JSON schema"))

    # Sort by path
    all_routes.sort(key=lambda item: item[1])

    print("\n" + "=" * 78)
    print(f"{'METHOD':<8} | {'PATH':<35} | {'SUMMARY'}")
    print("=" * 78)

    for method, path, summary in all_routes:
        print(f"{method:<8} | {path:<35} | {summary}")

    print("=" * 78)
    print(f"Total endpoints registered: {len(all_routes)}")

    print("\n" + "-" * 78)
    print("API DOCUMENTATION URLS:")
    print("-" * 78)
    if app.docs_url:
        print(f"  * Swagger UI:   {base_url}{app.docs_url}")
    if app.redoc_url:
        print(f"  * ReDoc:        {base_url}{app.redoc_url}")
    if app.openapi_url:
        print(f"  * OpenAPI JSON: {base_url}{app.openapi_url}")
    print("-" * 78 + "\n")


if __name__ == "__main__":
    print_routes()
