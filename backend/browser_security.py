"""Exact-origin browser policy and session-bound CSRF protection.

Machine clients such as the local telemetry bridge use explicit bearer credentials.
They never gain authority merely by sending an access cookie.
"""
import hashlib
import hmac
import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

SAFE_METHODS = frozenset(("GET", "HEAD", "OPTIONS"))


def canonical_origin(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        raise ValueError("Expected one exact http(s) app origin, without a path or credentials")
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    port = parsed.port
    suffix = f":{port}" if port and port != (443 if parsed.scheme == "https" else 80) else ""
    return f"{parsed.scheme}://{host}{suffix}"


def configured_app_origin() -> str:
    if os.environ.get("MCCOY_DESKTOP") == "1":
        origin = canonical_origin(os.environ["DESKTOP_APP_ORIGIN"])
        if urlsplit(origin).hostname not in ("127.0.0.1", "localhost", "::1"):
            raise RuntimeError("Desktop origin must be loopback")
        return origin
    configured = os.environ.get("REACT_APP_BACKEND_URL") or dotenv_values(
        Path(__file__).parent.parent / "frontend" / ".env"
    ).get("REACT_APP_BACKEND_URL")
    if not configured:
        raise RuntimeError("REACT_APP_BACKEND_URL must configure the trusted app origin")
    origin = canonical_origin(configured)
    if urlsplit(origin).scheme != "https":
        raise RuntimeError("Hosted browser sessions require an HTTPS app origin")
    return origin


def csrf_for_token(access_token: str) -> str:
    return hmac.new(os.environ["JWT_SECRET"].encode(), b"mccoy-csrf-v1:" + access_token.encode(), hashlib.sha256).hexdigest()


def secure_cookie() -> bool:
    return os.environ.get("MCCOY_DESKTOP") != "1"


class AppCORSMiddleware(CORSMiddleware):
    """Never advertise credential sharing to an origin outside the exact allowlist."""
    def preflight_response(self, request_headers):
        response = super().preflight_response(request_headers)
        if not self.is_allowed_origin(request_headers["origin"]):
            if "access-control-allow-credentials" in response.headers:
                del response.headers["access-control-allow-credentials"]
        return response

    async def simple_response(self, scope, receive, send, request_headers):
        if not self.is_allowed_origin(request_headers["origin"]):
            return await self.app(scope, receive, send)
        return await super().simple_response(scope, receive, send, request_headers)


class BrowserSecurityMiddleware:
    def __init__(self, app, trusted_origin: str):
        self.app = app
        self.trusted_origin = trusted_origin

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            return await self.app(scope, receive, send)
        request = Request(scope)
        origin = request.headers.get("origin")
        fetch_site = request.headers.get("sec-fetch-site", "")
        unsafe = request.method not in SAFE_METHODS
        bearer = request.headers.get("authorization", "").startswith("Bearer ")
        cookie = request.cookies.get("access_token")

        async def reject(detail, code="untrusted_origin", status=403):
            return await JSONResponse({"detail": detail, "code": code}, status_code=status,
                                      headers={"Cache-Control": "no-store"})(scope, receive, send)

        # Validate a supplied origin even on bearer requests. Non-browser clients
        # have no Origin and still require their normal authenticated bearer token.
        if origin is not None:
            try:
                allowed = canonical_origin(origin) == self.trusted_origin
            except ValueError:
                allowed = False
            if not allowed:
                return await reject("This website is not allowed to access the app")
        elif fetch_site in ("cross-site", "same-site"):
            return await reject("Cross-site browser requests are not allowed")

        if unsafe and scope["path"] == "/api/auth/login":
            if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                return await reject("Login requires application/json", "invalid_content_type", 415)

        if unsafe and cookie and not bearer and scope["path"] != "/api/auth/login":
            supplied = request.headers.get("x-csrf-token", "")
            expected = csrf_for_token(cookie)
            if not supplied or not hmac.compare_digest(supplied.encode(), expected.encode()):
                return await reject("Session verification failed. Please retry.", "csrf_failed")

        # Sensitive API responses must not remain in browser/shared caches.
        async def no_store(message):
            if message["type"] == "http.response.start":
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"cache-control"]
                headers.append((b"cache-control", b"no-store"))
                message["headers"] = headers
            await send(message)

        return await self.app(scope, receive, no_store)