import json
import os
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from pydantic import BaseModel, Field, ConfigDict, ValidationError, field_validator
from dotenv import dotenv_values
from starlette.concurrency import run_in_threadpool
from auth import get_current_user, require_owner
from db import get_conn, one, rows
from telemetry_engine import ingest


class Game(BaseModel):
    connected: bool
    paused: bool = False
    gameName: str = Field(default="Unknown", max_length=40)
    time: Optional[str] = Field(default=None, max_length=80)


class Truck(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    fuel: Optional[float] = Field(default=None, ge=0, le=10000)
    fuelCapacity: Optional[float] = Field(default=None, ge=0, le=10000)
    odometer: Optional[float] = Field(default=None, ge=0, le=1e9)
    speed: Optional[float] = None


class Job(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    sourceCity: Optional[str] = Field(default=None, max_length=200)
    destinationCity: Optional[str] = Field(default=None, max_length=200)
    sourceCompany: Optional[str] = Field(default=None, max_length=200)
    destinationCompany: Optional[str] = Field(default=None, max_length=200)
    income: Optional[float] = Field(default=None, ge=0, le=1e10)
    deadlineTime: Optional[str] = Field(default=None, max_length=80)


class Trailer(BaseModel):
    attached: bool = False
    name: Optional[str] = Field(default=None, max_length=200)


class Snapshot(BaseModel):
    game: Game
    truck: Truck = Field(default_factory=Truck)
    job: Job = Field(default_factory=Job)
    trailer: Trailer = Field(default_factory=Trailer)


class Sample(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    sequence: int = Field(ge=0)
    raw: Snapshot


class Settings(BaseModel):
    driver_id: int
    truck_id: int
    server_url: str = Field(max_length=300)
    enabled: bool

    @field_validator("server_url")
    @classmethod
    def local_only(cls, value):
        url = urlparse(value)
        if url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost", "::1") or url.username or url.password or url.fragment:
            raise ValueError("Use the local HTTP telemetry server on this PC (localhost or 127.0.0.1)")
        if url.path.rstrip("/") != "/api/ets2/telemetry":
            raise ValueError("Expected Funbit endpoint /api/ets2/telemetry")
        return value


class Review(BaseModel):
    action: Literal["approve", "dismiss"]
    record: dict = Field(default_factory=dict)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Telemetry redirects are not allowed")


def build_router(LoadIn, FuelIn, prep_fuel, sync_load_income, insert):
    router = APIRouter(prefix="/api/telemetry")

    @router.get("/status")
    def status(user=Depends(get_current_user)):
        with get_conn() as conn:
            source = one(conn, "SELECT * FROM telemetry_sources WHERE user_id=?", (user["id"],))
        if source:
            state = json.loads(source.pop("state"))
            source["live"] = state.get("previous")
        return {"source": source, "desktop": os.environ.get("MCCOY_DESKTOP") == "1"}

    @router.put("/settings")
    def settings(body: Settings, user=Depends(get_current_user)):
        with get_conn() as conn:
            if not one(conn, "SELECT id FROM drivers WHERE id=?", (body.driver_id,)) or not one(conn, "SELECT id FROM trucks WHERE id=?", (body.truck_id,)):
                raise HTTPException(400, "Select an existing driver and truck")
            conn.execute("""INSERT INTO telemetry_sources (user_id,driver_id,truck_id,server_url,enabled) VALUES (?,?,?,?,?)
                ON CONFLICT(user_id) DO UPDATE SET driver_id=excluded.driver_id,truck_id=excluded.truck_id,
                server_url=excluded.server_url,enabled=excluded.enabled,state='{}',last_seen=NULL""",
                (user["id"], body.driver_id, body.truck_id, body.server_url, int(body.enabled)))
        return {"ok": True}

    @router.post("/ingest")
    async def incoming(request: Request, user=Depends(get_current_user)):
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 128 * 1024:
                raise HTTPException(413, "Telemetry snapshot too large")
        try:
            sample = Sample.model_validate_json(raw)
        except ValidationError:
            raise HTTPException(422, "Invalid Funbit telemetry snapshot")
        def save_sample():
            with get_conn() as conn:
                return ingest(conn, user["id"], sample)
        return await run_in_threadpool(save_sample)

    @router.post("/local-poll")
    def local_poll(user=Depends(get_current_user)):
        if os.environ.get("MCCOY_DESKTOP") != "1":
            raise HTTPException(400, "Use the local bridge when accessing McCoy online")
        with get_conn() as conn:
            source = one(conn, "SELECT * FROM telemetry_sources WHERE user_id=?", (user["id"],))
        if not source or not source["enabled"]:
            return {"accepted": False}
        Settings.model_validate(source)
        try:
            url = source["server_url"] + ("&" if "?" in source["server_url"] else "?") + f"ts={time.time_ns()}"
            with urllib.request.build_opener(NoRedirect).open(url, timeout=2) as response:
                raw = json.loads(response.read(128 * 1024))
            sample = Sample(session_id=f"desktop-{user['id']}", sequence=time.time_ns(), raw=raw)
        except Exception:
            raise HTTPException(503, "Local telemetry server is unavailable or returned unsupported data")
        with get_conn() as conn:
            return ingest(conn, user["id"], sample)

    @router.get("/bridge")
    def bridge(request: Request, user=Depends(get_current_user)):
        configured = os.environ.get("REACT_APP_BACKEND_URL") or dotenv_values(Path(__file__).parent.parent / "frontend" / ".env").get("REACT_APP_BACKEND_URL")
        parsed = urlparse(str(request.base_url))
        app_url = configured.rstrip("/") if configured else None
        if os.environ.get("MCCOY_DESKTOP") == "1" and parsed.hostname in ("localhost", "127.0.0.1", "::1"):
            app_url = str(request.base_url).rstrip("/")
        # Without a configured public address, the standalone bridge asks locally.
        # Never embed a reverse proxy's private/re-written Host in a download.
        script = Path(__file__).with_name("telemetry_bridge.py").read_text()
        script = script.replace("DEFAULT_APP_URL = None", f"DEFAULT_APP_URL = {app_url!r}", 1)
        return Response(script, media_type="text/x-python", headers={"Content-Disposition": 'attachment; filename="McCoyTelemetry.py"'})

    @router.get("/launcher")
    def launcher(user=Depends(get_current_user)):
        script = '@echo off\r\ncd /d "%~dp0"\r\ntitle McCoy Telemetry\r\nif not exist "McCoyTelemetry.py" (\r\n echo Download McCoyTelemetry.py into this same folder first.\r\n pause\r\n exit /b 1\r\n)\r\nwhere py >nul 2>nul\r\nif not errorlevel 1 (\r\n py -3 McCoyTelemetry.py\r\n) else (\r\n where python >nul 2>nul\r\n if errorlevel 1 (\r\n  echo Python is not installed. Install Python 3.10 or newer from python.org and enable Add Python to PATH.\r\n ) else (\r\n  python McCoyTelemetry.py\r\n )\r\n)\r\npause\r\n'
        return Response(script, media_type="application/octet-stream", headers={"Content-Disposition": 'attachment; filename="StartMcCoyTelemetry.bat"'})

    @router.get("/events")
    def events(user=Depends(get_current_user)):
        with get_conn() as conn:
            where, args = ("", ()) if user["role"] == "owner" else ("WHERE user_id=?", (user["id"],))
            result = rows(conn, f"SELECT * FROM telemetry_events {where} ORDER BY id DESC", args)
        return [{**r, "payload": json.loads(r["payload"])} for r in result]

    @router.get("/manage-events", dependencies=[Depends(require_owner)])
    def manage_events(q: str = Query(default="", max_length=200), offset: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=100)):
        query = "%" + q.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        where = """WHERE casefold(kind || ' ' || status || ' ' || detected_at || ' ' || id) LIKE ? ESCAPE '\\'
            OR EXISTS (SELECT 1 FROM json_tree(telemetry_events.payload)
                WHERE type IN ('text','integer','real') AND casefold(atom) LIKE ? ESCAPE '\\')"""
        with get_conn() as conn:
            conn.create_function("casefold", 1, lambda value: str(value).casefold() if value is not None else "", deterministic=True)
            total = one(conn, f"SELECT COUNT(*) AS n FROM telemetry_events {where}", (query, query))["n"]
            result = rows(conn, f"SELECT * FROM telemetry_events {where} ORDER BY id DESC LIMIT ? OFFSET ?", (query, query, limit, offset))
        return {"items": [{**r, "payload": json.loads(r["payload"])} for r in result], "total": total, "offset": offset, "limit": limit}

    @router.post("/events/{event_id}/review")
    def review(event_id: int, body: Review, user=Depends(get_current_user)):
        with get_conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            event = one(conn, "SELECT * FROM telemetry_events WHERE id=?", (event_id,))
            if not event or (user["role"] != "owner" and event["user_id"] != user["id"]):
                raise HTTPException(404, "Detection not found")
            if event["status"] != "pending":
                raise HTTPException(409, "This detection has already been reviewed")
            record_id = None
            if body.action == "approve":
                try:
                    model = LoadIn if event["kind"] == "load" else FuelIn
                    record = model.model_validate(body.record).model_dump()
                    numeric = [v for v in record.values() if isinstance(v, float)]
                    import math
                    if not all(math.isfinite(v) for v in numeric):
                        raise ValueError()
                    from datetime import date
                    date.fromisoformat(record["delivered_date"] if event["kind"] == "load" else record["date"])
                    if event["kind"] == "load" and (not body.record.get("status") or record["pay"] < 0):
                        raise ValueError()
                except (ValidationError, ValueError, TypeError):
                    raise HTTPException(422, "Complete the record: delivery date and status for loads, purchase date and positive price for fuel")
                for field, table in (("driver_id", "drivers"), ("truck_id", "trucks")):
                    if not record.get(field) or not one(conn, f"SELECT id FROM {table} WHERE id=?", (record[field],)):
                        raise HTTPException(400, "Select an existing driver and truck")
                if event["kind"] == "fuel":
                    if not record.get("gallons"):
                        raise HTTPException(422, "Confirm the gallons purchased")
                    record = prep_fuel(conn, record)
                record_id = insert(conn, "loads" if event["kind"] == "load" else "fuel", record)
                if event["kind"] == "load":
                    sync_load_income(conn, record_id)
            conn.execute("UPDATE telemetry_events SET status=?,record_id=?,reviewed_by=? WHERE id=?",
                ("approved" if body.action == "approve" else "dismissed", record_id, user["id"], event_id))
        return {"ok": True, "record_id": record_id}

    @router.delete("/events/{event_id}", dependencies=[Depends(require_owner)])
    def delete_event(event_id: int):
        with get_conn() as conn:
            if not one(conn, "SELECT id FROM telemetry_events WHERE id=?", (event_id,)):
                raise HTTPException(404, "Detection not found")
            conn.execute("DELETE FROM telemetry_events WHERE id=?", (event_id,))
        return {"ok": True}

    return router