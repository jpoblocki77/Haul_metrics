"""McCoy Trucking desktop launcher: runs the app locally and opens it in its own window."""
import os
import secrets
import socket
import sys
import threading
import time
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
ROOT = Path(sys._MEIPASS) if FROZEN else Path(__file__).parent
DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "McCoyTrucking" if FROZEN else ROOT
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _secret():
    f = DATA_DIR / "secret.key"
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip()


PORT = 8765
os.environ.setdefault("SQLITE_DB_FILE", str(DATA_DIR / "fleet.db"))
os.environ.setdefault("JWT_SECRET", _secret())
os.environ.setdefault("OWNER_USERNAME", "owner")
os.environ.setdefault("OWNER_PASSWORD", "trucker123")
os.environ.setdefault("CORS_ORIGINS", f"http://127.0.0.1:{PORT}")

import uvicorn  # noqa: E402
import webview  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from server import app  # noqa: E402

BUILD = ROOT / "frontend_build" if FROZEN else ROOT.parent / "frontend" / "build"
if not BUILD.exists():
    raise SystemExit("Frontend build not found. Run: cd frontend && REACT_APP_BACKEND_URL= yarn build")

app.mount("/static", StaticFiles(directory=BUILD / "static"), name="static")


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str):
    f = BUILD / path
    return FileResponse(f if path and f.is_file() else BUILD / "index.html")


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning", log_config=None)


def wait_for_server(timeout=15):
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", PORT)) == 0:
                return
        time.sleep(0.2)


if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    wait_for_server()
    webview.create_window("McCoy Trucking", f"http://127.0.0.1:{PORT}", width=1440, height=900, min_size=(1024, 700))
    webview.start()
