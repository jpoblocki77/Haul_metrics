"""Local SCS/Funbit telemetry bridge. Python 3.10+; no extra packages required."""
import getpass
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

DEFAULT_APP_URL = 'https://haul-metrics-2.preview.emergentagent.com'  # Injected into the downloaded copy, never includes credentials.
LOG_PATH = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "McCoyTrucking" / "telemetry-bridge.log"


def request(url, body=None, token=None):
    headers = {"Content-Type": "application/json", "User-Agent": "McCoyTelemetry/1.1 (Python; VTC telemetry bridge)", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers)
    with urlopen(req, timeout=8) as response:
        return json.loads(response.read(128 * 1024))


def safe_url(value):
    parsed = urlparse(value.strip())
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Enter the app's base address, without account details or a page path.")
    local = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme not in ("http", "https"):
        raise ValueError("The app address must start with https:// (or http:// for localhost).")
    # Reverse proxies may report internal HTTP. Never send sign-in details over public HTTP.
    scheme = parsed.scheme if local else "https"
    return f"{scheme}://{parsed.netloc}".rstrip("/")


def sign_in(app_url):
    while True:
        username = input("McCoy username: ").strip()
        password = getpass.getpass("McCoy password: ")
        try:
            result = request(app_url + "/api/auth/login", {"username": username, "password": password})
            return result["token"]
        except HTTPError as exc:
            if exc.code == 401:
                print("Incorrect username or password. Please try again.", flush=True)
            elif exc.code == 429:
                raise RuntimeError("Too many sign-in attempts. Wait 15 minutes, then restart.") from None
            else:
                raise RuntimeError(f"The app could not sign you in (HTTP {exc.code}).") from None
        except (URLError, TimeoutError):
            raise RuntimeError("Cannot reach the McCoy app. Check your internet connection and app address.") from None
        finally:
            del password


def main(app_url=None):
    print("McCoy Trucking — SCS telemetry bridge\nKeep this window open while driving.", flush=True)
    app_url = safe_url(app_url or input("McCoy app URL: "))
    print(f"Connecting to {app_url}", flush=True)
    token = sign_in(app_url)
    session, sequence, previous_message = uuid.uuid4().hex, 0, None
    print("Signed in. Ctrl+C stops the bridge.", flush=True)
    while True:
        try:
            source = request(app_url + "/api/telemetry/status", token=token).get("source")
            if not source or not source["enabled"]:
                message = "Open Live Telemetry in McCoy, select your driver/truck, enable detection, and save."
            else:
                url = source["server_url"]
                local = urlparse(url)
                if local.scheme != "http" or local.hostname not in ("localhost", "127.0.0.1", "::1"):
                    raise ValueError("Telemetry must run on this PC")
                raw = request(url + ("&" if "?" in url else "?") + f"ts={time.time_ns()}")
                sequence += 1
                request(app_url + "/api/telemetry/ingest", {"session_id": session, "sequence": sequence, "raw": raw}, token)
                message = "Receiving game telemetry. Detections wait for review in McCoy." if raw.get("game", {}).get("connected") else "Server connected. Load your ETS2 / ATS game profile."
            if message != previous_message:
                print(message, flush=True)
                previous_message = message
            time.sleep(1)
        except HTTPError as exc:
            if exc.code == 401:
                raise RuntimeError("Your session expired or the account changed. Restart to sign in again.") from None
            message = f"Connection returned HTTP {exc.code}. Check server settings; retrying in 3 seconds."
            if message != previous_message:
                print(message, flush=True)
                previous_message = message
            time.sleep(3)
        except (URLError, TimeoutError, ValueError, OSError):
            message = "Waiting for the local SCS server or app connection. Start Ets2Telemetry.exe and your game. Retrying…"
            if message != previous_message:
                print(message, flush=True)
                previous_message = message
            time.sleep(3)


def launch(app_url=None):
    """Double-click entrypoint: startup errors remain visible instead of closing the console."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s %(message)s")
        if sys.stdin is None or sys.stdout is None:
            raise RuntimeError("Open with Python (python.exe), not pythonw.exe, or use StartMcCoyTelemetry.bat.")
        main(app_url)
    except KeyboardInterrupt:
        print("\nBridge stopped. Your saved detections remain in McCoy.", flush=True)
    except Exception as exc:
        # Do not log credentials, tokens, request bodies, or arbitrary remote response content.
        logging.error("Bridge stopped: %s", type(exc).__name__)
        message = f"Bridge could not continue: {exc}\nLog: {LOG_PATH}\nUse StartMcCoyTelemetry.bat to keep this window open."
        if sys.stdout is not None:
            print(message, flush=True)
        elif os.name == "nt":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "McCoy Telemetry", 0x10)
    finally:
        try:
            input("Press Enter to close this window…")
        except (EOFError, KeyboardInterrupt, RuntimeError):
            pass


if __name__ == "__main__":
    launch(DEFAULT_APP_URL)