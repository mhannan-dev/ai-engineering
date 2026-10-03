"""
High-Performance Code Transpiler
Project entrypoint exposing FastAPI app and standalone uvicorn runner.
"""

from api.main import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
