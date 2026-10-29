from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from auth import require_owner, verify_password
from db import get_conn, one

DEFAULT_BRANDING = {"company_name": "McCoy Trucking", "primary_color": "#3b82f6", "accent_color": "#dc2626", "dark_background": "#0b0f17", "light_background": "#f5f7fa"}


class CompanyIn(BaseModel):
    company_name: str = Field(min_length=1, max_length=60)
    primary_color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    dark_background: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    light_background: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("company_name")
    @classmethod
    def trimmed_name(cls, value):
        value = value.strip()
        if not value or any(ord(c) < 32 for c in value):
            raise ValueError("Enter a company name without control characters")
        return value

    @field_validator("dark_background", "light_background")
    @classmethod
    def readable_background(cls, value, info):
        rgb = [int(value[i:i+2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
        luminance = sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))
        if info.field_name == "dark_background" and luminance > .15:
            raise ValueError("Choose a darker background for readable dark mode")
        if info.field_name == "light_background" and luminance < .6:
            raise ValueError("Choose a lighter background for readable light mode")
        return value.lower()


router = APIRouter(prefix="/api/company")


@router.get("/branding")
def branding():
    # Public appearance only, so the sign-in page can show the company name.
    with get_conn() as conn:
        stored = one(conn, "SELECT company_name,primary_color,accent_color,dark_background,light_background FROM company_settings WHERE id=1")
    return stored or DEFAULT_BRANDING.copy()


@router.put("/branding", dependencies=[Depends(require_owner)])
def save_branding(body: CompanyIn):
    payload = body.model_dump()
    with get_conn() as conn:
        conn.execute("""INSERT INTO company_settings (id,company_name,primary_color,accent_color,dark_background,light_background)
            VALUES (1,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET company_name=excluded.company_name,
            primary_color=excluded.primary_color,accent_color=excluded.accent_color,
            dark_background=excluded.dark_background,light_background=excluded.light_background""", list(payload.values()))
    return payload


# Reset recorded activity only; preserve fleet setup, active connections and accounts.
RECORD_TABLES = ("telemetry_events", "income", "expenses", "fuel", "inspections", "loads")


class EraseIn(BaseModel):
    confirmation: str
    owner_password: str = Field(min_length=1, max_length=72)


@router.get("/record-counts", dependencies=[Depends(require_owner)])
def record_counts():
    with get_conn() as conn:
        return {table: one(conn, f"SELECT COUNT(*) AS n FROM {table}")["n"] for table in RECORD_TABLES}


@router.post("/erase-records")
def erase_records(body: EraseIn, user=Depends(require_owner)):
    if body.confirmation != "ERASE ALL RECORDS":
        raise HTTPException(400, "Type ERASE ALL RECORDS to confirm")
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        account = one(conn, "SELECT password_hash,role FROM users WHERE id=?", (user["id"],))
        if not account or account["role"] != "owner" or not verify_password(body.owner_password, account["password_hash"]):
            raise HTTPException(403, "Current owner password is incorrect")
        removed = {table: one(conn, f"SELECT COUNT(*) AS n FROM {table}")["n"] for table in RECORD_TABLES}
        for table in RECORD_TABLES:
            conn.execute(f"DELETE FROM {table}")
    return {"ok": True, "removed": removed, "preserved": ["user accounts", "company branding", "expense categories", "drivers", "trucks", "telemetry connections"]}