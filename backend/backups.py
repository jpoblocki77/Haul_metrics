"""Portable encrypted company archives; never execute SQL from an uploaded file."""
import base64
import json
import math
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone, date
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, ValidationError
from auth import require_owner, verify_password
from db import get_conn, one, rows, SCHEMA, TELEMETRY_SCHEMA

router = APIRouter(prefix="/api/backup", dependencies=[Depends(require_owner)])
TABLES = ("users", "company_settings", "categories", "trucks", "drivers", "loads", "income", "expenses", "fuel", "inspections", "telemetry_sources", "telemetry_events")
MAGIC = b"MCCOY-BACKUP-1\n"
MAX_BYTES = 25 * 1024 * 1024


class ExportIn(BaseModel):
    passphrase: str = Field(min_length=12, max_length=256)


class ImportIn(ExportIn):
    archive: str = Field(max_length=MAX_BYTES)
    confirm: str = ""
    owner_password: str = ""


async def import_body(request: Request):
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > MAX_BYTES:
            raise HTTPException(413, "Backup exceeds the 25 MB upload limit")
    try:
        return ImportIn.model_validate_json(raw)
    except (ValidationError, ValueError):
        raise HTTPException(422, "Invalid backup request")


def cipher(passphrase, salt):
    key = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(passphrase.encode())
    return Fernet(base64.urlsafe_b64encode(key))


def unpack(body):
    try:
        blob = base64.b64decode(body.archive, validate=True)
        if not blob.startswith(MAGIC):
            raise ValueError()
        offset = len(MAGIC)
        salt, token = blob[offset:offset + 16], blob[offset + 16:]
        data = json.loads(cipher(body.passphrase, salt).decrypt(token))
        if not isinstance(data, dict) or data.get("format") != "mccoy-company" or type(data.get("version")) is not int or data["version"] != 1:
            raise ValueError()
        if not isinstance(data.get("created_at"), str) or not isinstance(data.get("tables"), dict):
            raise ValueError()
        created_at = datetime.fromisoformat(data["created_at"])
        if created_at.tzinfo is None:
            raise ValueError()
        data["tables"].setdefault("company_settings", [])
        validate_records(data["tables"])
        return data
    except (ValueError, KeyError, TypeError, InvalidToken, sqlite3.Error, OverflowError):
        raise HTTPException(400, "Incorrect backup password, damaged file, or unsupported backup")


def validate_records(tables):
    if not isinstance(tables, dict) or set(tables) != set(TABLES):
        raise ValueError()
    scratch = sqlite3.connect(":memory:")
    try:
        scratch.execute("PRAGMA foreign_keys = ON")
        scratch.executescript(SCHEMA + TELEMETRY_SCHEMA)
        for table in TABLES:
            schema = scratch.execute(f"PRAGMA table_info({table})").fetchall()
            columns = {r[1] for r in schema}
            if not isinstance(tables[table], list):
                raise ValueError()
            for record in tables[table]:
                if not isinstance(record, dict) or set(record) != columns:
                    raise ValueError()
                for _, key, dtype, required, _, primary_key in schema:
                    value = record[key]
                    if value is None:
                        if required or primary_key:
                            raise ValueError()
                        continue
                    if dtype == "INTEGER" and (type(value) is not int or (key.endswith("id") and value < 1)):
                        raise ValueError()
                    if dtype == "REAL" and (type(value) not in (int, float) or not math.isfinite(value)):
                        raise ValueError()
                    if dtype == "TEXT" and (not isinstance(value, str) or len(value) > 200000):
                        raise ValueError()
                if record.get("is_test", 0) not in (0, 1):
                    raise ValueError()
                for field in ("date", "due_date", "delivered_date"):
                    if record.get(field) is not None and date.fromisoformat(record[field]).isoformat() != record[field]:
                        raise ValueError()
                if table == "company_settings":
                    from company import CompanyIn
                    CompanyIn.model_validate({k: v for k, v in record.items() if k != "id"})
                if table == "users":
                    if record["role"] not in ("owner", "dispatcher") or not re.fullmatch(r"[a-z0-9_.-]{3,32}", record["username"]):
                        raise ValueError()
                    if not re.fullmatch(r"\$2[aby]\$(0[4-9]|[12][0-9]|3[01])\$[./A-Za-z0-9]{53}", record["password_hash"]):
                        raise ValueError()
                if table == "loads" and record["status"] not in ("On Time", "Late"):
                    raise ValueError()
                if table == "inspections" and record["result"] not in ("Passed", "Fined", "Out of Service"):
                    raise ValueError()
                if table == "trucks" and record["tank_gallons"] <= 0:
                    raise ValueError()
                if table == "fuel" and (record["gallons"] <= 0 or record["price_per_gallon"] <= 0):
                    raise ValueError()
                if table == "telemetry_events":
                    if record["kind"] not in ("load", "fuel") or record["status"] not in ("pending", "approved", "dismissed") or not isinstance(json.loads(record["payload"]), dict):
                        raise ValueError()
                if table == "telemetry_sources" and not isinstance(json.loads(record["state"]), dict):
                    raise ValueError()
                keys = list(record)
                scratch.execute(f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})", list(record.values()))
        if not scratch.execute("SELECT 1 FROM users WHERE role='owner'").fetchone() or scratch.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError()
    finally:
        scratch.close()


@router.post("/export")
def export_backup(body: ExportIn):
    with get_conn() as conn:
        conn.execute("BEGIN")
        tables = {t: rows(conn, f"SELECT * FROM {t}") for t in TABLES}
    # Do not transfer a live device connection or stale detector baseline to another PC.
    for source in tables["telemetry_sources"]:
        source.update(state="{}", enabled=0, last_seen=None)
    data = {"format": "mccoy-company", "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "tables": tables}
    salt = os.urandom(16)
    blob = MAGIC + salt + cipher(body.passphrase, salt).encrypt(json.dumps(data, allow_nan=False).encode())
    if len(base64.b64encode(blob)) > MAX_BYTES - 4096:
        raise HTTPException(413, "Company archive exceeds the portable backup size limit")
    return Response(blob, media_type="application/octet-stream", headers={
        "Content-Disposition": 'attachment; filename="mccoy-company.mccoy"', "Cache-Control": "no-store"})


@router.post("/inspect")
def inspect_backup(body: ImportIn = Depends(import_body)):
    data = unpack(body)
    return {"created_at": data["created_at"], "counts": {t: len(data["tables"][t]) for t in TABLES},
            "owners": [u["username"] for u in data["tables"]["users"] if u["role"] == "owner"]}


@router.post("/restore")
def restore_backup(body: ImportIn = Depends(import_body), user=Depends(require_owner)):
    if body.confirm != "RESTORE MCCOY":
        raise HTTPException(400, "Explicit restore confirmation is required")
    data = unpack(body)
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = one(conn, "SELECT password_hash FROM users WHERE id = ?", (user["id"],))
        if not current or not verify_password(body.owner_password, current["password_hash"]):
            raise HTTPException(403, "Current owner password is incorrect")
        for table in reversed(TABLES):
            conn.execute(f"DELETE FROM {table}")
        for table in TABLES:
            for row in data["tables"][table]:
                if table == "users":
                    row["session_version"] = uuid.uuid4().hex
                if table == "telemetry_sources":
                    row.update(state="{}", enabled=0, last_seen=None)
                keys = list(row)
                conn.execute(f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})", list(row.values()))
    return {"ok": True, "sign_in_required": True}