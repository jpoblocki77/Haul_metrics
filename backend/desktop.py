"""McCoy Trucking desktop launcher: runs the app locally and opens it in its own window."""
import os
import secrets
import threading
import time
from pathlib import Path

ROOT = Path(__file__).parent
os.environ.setdefault("SQLITE_DB_FILE", "fleet.db")
os.environ.setdefault("JWT_SECRET", secrets.token_hex(32))
os.environ.setdefault("OWNER_USERNAME", "owner")
os.environ.setdefault("OWNER_PASSWORD", "trucker123")
os.environ.setdefault("CORS_ORIGINS", "http://127.0.0.1:8765")

import uvicorn  # noqa: E402
import webview  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from server import app  # noqa: E402

BUILD = ROOT.parent / "frontend" / "build"
PORT = 8765

if not BUILD.exists():
    raise SystemExit("Frontend build not found. Run: cd frontend && REACT_APP_BACKEND_URL= yarn build")

app.mount("/static", StaticFiles(directory=BUILD / "static"), name="static")


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str):
    f = BUILD / path
    return FileResponse(f if path and f.is_file() else BUILD / "index.html")


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(1.5)
    webview.create_window("McCoy Trucking", f"http://127.0.0.1:{PORT}", width=1440, height=900, min_size=(1024, 700))
    webview.start()
