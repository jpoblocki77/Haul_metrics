from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

import os
import io
import csv
import sqlite3
import logging
from typing import Optional, Literal
from datetime import date

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Response
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from db import get_conn, rows, one, init_db
from auth import hash_password, verify_password, create_token, get_current_user, seed_owner
from seed import seed_test_data, clear_test_data, test_data_status

app = FastAPI()
api = APIRouter(prefix="/api")
secure = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])
logger = logging.getLogger(__name__)


# ---------- Models ----------
class LoginIn(BaseModel):
    username: str
    password: str


class CategoryIn(BaseModel):
    name: str = Field(min_length=1)


class TruckIn(BaseModel):
    truck_number: str = Field(min_length=1)
    tank_gallons: float = Field(gt=0)
    make_model: Optional[str] = None


class DriverIn(BaseModel):
    name: str = Field(min_length=1)
    notes: Optional[str] = None


class IncomeIn(BaseModel):
    date: str
    amount: float
    source: str = Field(min_length=1)
    driver_id: Optional[int] = None
    truck_id: Optional[int] = None
    notes: Optional[str] = None


class ExpenseIn(BaseModel):
    date: str
    amount: float
    category_id: Optional[int] = None
    driver_id: Optional[int] = None
    truck_id: Optional[int] = None
    description: Optional[str] = None


class FuelIn(BaseModel):
    date: str
    truck_id: int
    driver_id: Optional[int] = None
    gallons: Optional[float] = Field(default=None, gt=0)
    price_per_gallon: float = Field(gt=0)
    miles: Optional[float] = Field(default=None, ge=0)
    location: Optional[str] = None


class LoadIn(BaseModel):
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    cargo: Optional[str] = None
    driver_id: Optional[int] = None
    truck_id: Optional[int] = None
    pay: float = 0
    miles: Optional[float] = None
    due_date: Optional[str] = None
    delivered_date: Optional[str] = None
    status: Literal["On Time", "Late"] = "On Time"


class InspectionIn(BaseModel):
    date: str
    driver_id: Optional[int] = None
    truck_id: Optional[int] = None
    location: Optional[str] = None
    result: Literal["Passed", "Fined", "Out of Service"]
    fine_amount: Optional[float] = None
    fine_reason: Optional[str] = None
    notes: Optional[str] = None


# ---------- Generic CRUD ----------
JOINS = {
    "driver_id": ("LEFT JOIN drivers d ON d.id = x.driver_id", "d.name AS driver_name"),
    "truck_id": ("LEFT JOIN trucks t ON t.id = x.truck_id", "t.truck_number AS truck_number"),
    "category_id": ("LEFT JOIN categories c ON c.id = x.category_id", "c.name AS category_name"),
}
ORDER = {"income": "x.date DESC, x.id DESC", "expenses": "x.date DESC, x.id DESC", "fuel": "x.date DESC, x.id DESC",
         "loads": "COALESCE(x.delivered_date, x.due_date) DESC, x.id DESC", "inspections": "x.date DESC, x.id DESC",
         "trucks": "x.truck_number", "drivers": "x.name", "categories": "x.name"}
FKS = {"income": ["driver_id", "truck_id"], "expenses": ["category_id", "driver_id", "truck_id"],
       "fuel": ["driver_id", "truck_id"], "loads": ["driver_id", "truck_id"], "inspections": ["driver_id", "truck_id"],
       "trucks": [], "drivers": [], "categories": []}


def list_table(conn, table, where="", params=()):
    joins = [JOINS[f][0] for f in FKS[table]]
    cols = ["x.*"] + [JOINS[f][1] for f in FKS[table]]
    sql = f"SELECT {', '.join(cols)} FROM {table} x {' '.join(joins)} {where} ORDER BY {ORDER[table]}"
    return rows(conn, sql, params)


def get_row(conn, table, rid):
    r = list_table(conn, table, "WHERE x.id = ?", (rid,))
    if not r:
        raise HTTPException(404, "Not found")
    return r[0]


def insert(conn, table, data):
    keys = list(data.keys())
    cur = conn.execute(f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join('?' * len(keys))})",
                       [data[k] for k in keys])
    return cur.lastrowid


def update(conn, table, rid, data):
    one_or_404(conn, table, rid)
    conn.execute(f"UPDATE {table} SET {', '.join(f'{k} = ?' for k in data)} WHERE id = ?", [*data.values(), rid])


def one_or_404(conn, table, rid):
    r = one(conn, f"SELECT * FROM {table} WHERE id = ?", (rid,))
    if not r:
        raise HTTPException(404, "Not found")
    return r


def run(fn):
    try:
        with get_conn() as conn:
            return fn(conn)
    except sqlite3.IntegrityError as e:
        msg = "That value already exists" if "UNIQUE" in str(e) else "Invalid reference to another record"
        raise HTTPException(400, msg)


def register_crud(table, model, prepare=None, after_save=None):
    def _prep(conn, data, rid=None):
        return prepare(conn, data, rid) if prepare else data

    @secure.get(f"/{table}", name=f"list_{table}")
    def _list():
        return run(lambda c: list_table(c, table))

    @secure.post(f"/{table}", name=f"create_{table}")
    def _create(body: model):
        def fn(c):
            rid = insert(c, table, _prep(c, body.model_dump()))
            if after_save:
                after_save(c, rid)
            return get_row(c, table, rid)
        return run(fn)

    @secure.put(f"/{table}/{{rid}}", name=f"update_{table}")
    def _update(rid: int, body: model):
        def fn(c):
            update(c, table, rid, _prep(c, body.model_dump(), rid))
            if after_save:
                after_save(c, rid)
            return get_row(c, table, rid)
        return run(fn)

    @secure.delete(f"/{table}/{{rid}}", name=f"delete_{table}")
    def _delete(rid: int):
        def fn(c):
            one_or_404(c, table, rid)
            c.execute(f"DELETE FROM {table} WHERE id = ?", (rid,))
            return {"ok": True}
        return run(fn)


def prep_fuel(conn, data, rid=None):
    truck = one(conn, "SELECT tank_gallons FROM trucks WHERE id = ?", (data["truck_id"],))
    if not truck:
        raise HTTPException(400, "Truck not found")
    if not data.get("gallons"):
        data["gallons"] = truck["tank_gallons"]
    data["total"] = round(data["gallons"] * data["price_per_gallon"], 2)
    data["mpg"] = round(data["miles"] / data["gallons"], 2) if data.get("miles") else None
    return data


def prep_inspection(conn, data, rid=None):
    if data["result"] == "Passed":
        data["fine_amount"] = None
        data["fine_reason"] = None
    return data


def sync_load_income(conn, load_id):
    load = one(conn, "SELECT * FROM loads WHERE id = ?", (load_id,))
    payload = {"date": load["delivered_date"] or load["due_date"] or date.today().isoformat(), "amount": load["pay"],
               "source": f"Load: {load['origin']} → {load['destination']}", "driver_id": load["driver_id"],
               "truck_id": load["truck_id"], "load_id": load_id, "is_test": load["is_test"]}
    existing = one(conn, "SELECT id FROM income WHERE load_id = ?", (load_id,))
    if existing:
        payload.pop("is_test")
        update(conn, "income", existing["id"], payload)
    else:
        insert(conn, "income", payload)


register_crud("categories", CategoryIn)
register_crud("trucks", TruckIn)
register_crud("drivers", DriverIn)
register_crud("income", IncomeIn)
register_crud("expenses", ExpenseIn)
register_crud("fuel", FuelIn, prepare=prep_fuel)
register_crud("loads", LoadIn, after_save=sync_load_income)
register_crud("inspections", InspectionIn, prepare=prep_inspection)


# ---------- Auth ----------
@api.post("/auth/login")
def login(body: LoginIn, response: Response):
    with get_conn() as conn:
        user = one(conn, "SELECT * FROM users WHERE username = ?", (body.username.strip().lower(),))
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Wrong username or password")
    token = create_token(user["id"], user["username"])
    response.set_cookie("access_token", token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")
    return {"token": token, "user": {"id": user["id"], "username": user["username"]}}


@api.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api.get("/auth/me")
def me(user=Depends(get_current_user)):
    return user


# ---------- Stats ----------
def rng(col):
    return f"(:s IS NULL OR {col} >= :s) AND (:e IS NULL OR {col} <= :e)"


LOAD_DATE = "COALESCE(l.delivered_date, l.due_date)"


def driver_performance(conn, p):
    return rows(conn, f"""
        SELECT d.id, d.name, d.is_test,
          (SELECT COUNT(*) FROM loads l WHERE l.driver_id = d.id AND {rng(LOAD_DATE)}) AS loads,
          (SELECT COUNT(*) FROM loads l WHERE l.driver_id = d.id AND l.status = 'On Time' AND {rng(LOAD_DATE)}) AS on_time,
          (SELECT COUNT(*) FROM loads l WHERE l.driver_id = d.id AND l.status = 'Late' AND {rng(LOAD_DATE)}) AS late,
          (SELECT COALESCE(SUM(miles),0) FROM loads l WHERE l.driver_id = d.id AND {rng(LOAD_DATE)}) AS load_miles,
          (SELECT COALESCE(SUM(amount),0) FROM income i WHERE i.driver_id = d.id AND {rng('i.date')}) AS revenue,
          (SELECT COALESCE(SUM(gallons),0) FROM fuel f WHERE f.driver_id = d.id AND {rng('f.date')}) AS gallons,
          (SELECT SUM(miles) / SUM(gallons) FROM fuel f WHERE f.driver_id = d.id AND f.miles > 0 AND {rng('f.date')}) AS avg_mpg,
          (SELECT COUNT(*) FROM inspections n WHERE n.driver_id = d.id AND {rng('n.date')}) AS inspections,
          (SELECT COUNT(*) FROM inspections n WHERE n.driver_id = d.id AND n.result = 'Passed' AND {rng('n.date')}) AS passed,
          (SELECT COUNT(*) FROM inspections n WHERE n.driver_id = d.id AND n.result = 'Fined' AND {rng('n.date')}) AS fined,
          (SELECT COUNT(*) FROM inspections n WHERE n.driver_id = d.id AND n.result = 'Out of Service' AND {rng('n.date')}) AS oos,
          (SELECT COALESCE(SUM(fine_amount),0) FROM inspections n WHERE n.driver_id = d.id AND {rng('n.date')}) AS fines_total
        FROM drivers d ORDER BY d.name""", p)


def period(start: Optional[str] = None, end: Optional[str] = None):
    return {"s": start or None, "e": end or None}


@secure.get("/stats/drivers")
def stats_drivers(p=Depends(period)):
    with get_conn() as conn:
        return driver_performance(conn, p)


@secure.get("/stats/trucks")
def stats_trucks(p=Depends(period)):
    with get_conn() as conn:
        return rows(conn, f"""
            SELECT t.*, COUNT(f.id) AS fillups, COALESCE(SUM(f.gallons),0) AS gallons_bought,
              COALESCE(SUM(f.total),0) AS fuel_spend,
              SUM(CASE WHEN f.miles > 0 THEN f.miles END) / SUM(CASE WHEN f.miles > 0 THEN f.gallons END) AS avg_mpg,
              SUM(f.total) / NULLIF(SUM(f.gallons),0) AS avg_ppg
            FROM trucks t LEFT JOIN fuel f ON f.truck_id = t.id AND {rng('f.date')}
            GROUP BY t.id ORDER BY t.truck_number""", p)


def fuel_summary(conn, p):
    return one(conn, f"""SELECT COUNT(*) AS fillups, COALESCE(SUM(gallons),0) AS gallons, COALESCE(SUM(total),0) AS spend,
        SUM(total) / NULLIF(SUM(gallons),0) AS avg_ppg,
        SUM(CASE WHEN miles > 0 THEN miles END) / SUM(CASE WHEN miles > 0 THEN gallons END) AS avg_mpg
        FROM fuel WHERE {rng('date')}""", p)


def inspection_summary(conn, p):
    return {
        "by_result": rows(conn, f"SELECT result, COUNT(*) AS count FROM inspections WHERE {rng('date')} GROUP BY result", p),
        "by_reason": rows(conn, f"""SELECT fine_reason AS reason, COUNT(*) AS count, COALESCE(SUM(fine_amount),0) AS total
            FROM inspections WHERE fine_reason IS NOT NULL AND fine_reason != '' AND {rng('date')}
            GROUP BY fine_reason ORDER BY total DESC""", p),
        "fines_total": one(conn, f"SELECT COALESCE(SUM(fine_amount),0) AS v FROM inspections WHERE {rng('date')}", p)["v"],
    }


@secure.get("/stats/fuel")
def stats_fuel(p=Depends(period)):
    with get_conn() as conn:
        return fuel_summary(conn, p)


@secure.get("/stats/inspections")
def stats_inspections(p=Depends(period)):
    with get_conn() as conn:
        return inspection_summary(conn, p)


@secure.get("/stats/dashboard")
def stats_dashboard(p=Depends(period)):
    with get_conn() as conn:
        income = one(conn, f"SELECT COALESCE(SUM(amount),0) AS v FROM income WHERE {rng('date')}", p)["v"]
        other_exp = one(conn, f"SELECT COALESCE(SUM(amount),0) AS v FROM expenses WHERE {rng('date')}", p)["v"]
        fuel = fuel_summary(conn, p)
        insp = inspection_summary(conn, p)
        fines = insp["fines_total"]
        expenses = other_exp + fuel["spend"] + fines
        loads = one(conn, f"SELECT COUNT(*) AS total, SUM(l.status = 'On Time') AS on_time FROM loads l WHERE {rng(LOAD_DATE)}", p)
        monthly = rows(conn, f"""
            SELECT substr(date,1,7) AS m, SUM(inc) AS income, SUM(exp) AS expenses FROM (
              SELECT date, amount AS inc, 0 AS exp FROM income
              UNION ALL SELECT date, 0, amount FROM expenses
              UNION ALL SELECT date, 0, total FROM fuel
              UNION ALL SELECT date, 0, COALESCE(fine_amount,0) FROM inspections
            ) WHERE {rng('date')} AND date != '' GROUP BY m ORDER BY m""", p)
        by_cat = rows(conn, f"""SELECT COALESCE(c.name,'Uncategorized') AS name, SUM(e.amount) AS value
            FROM expenses e LEFT JOIN categories c ON c.id = e.category_id WHERE {rng('e.date')} GROUP BY c.name""", p)
        if fuel["spend"]:
            by_cat.append({"name": "Fuel", "value": fuel["spend"]})
        if fines:
            by_cat.append({"name": "DOT Fines", "value": fines})
        by_cat.sort(key=lambda r: -r["value"])
        fuel_trend = rows(conn, f"""SELECT substr(date,1,7) AS m, SUM(total) AS cost, SUM(gallons) AS gallons,
            SUM(total)/SUM(gallons) AS avg_ppg,
            SUM(CASE WHEN miles > 0 THEN miles END) / SUM(CASE WHEN miles > 0 THEN gallons END) AS avg_mpg
            FROM fuel WHERE {rng('date')} GROUP BY m ORDER BY m""", p)
        return {
            "income": income, "expenses": expenses, "profit": income - expenses, "fuel": fuel,
            "fines_total": fines, "loads_total": loads["total"], "loads_on_time": loads["on_time"] or 0,
            "on_time_rate": (loads["on_time"] or 0) / loads["total"] * 100 if loads["total"] else None,
            "monthly": monthly, "by_category": by_cat, "fuel_trend": fuel_trend,
            "drivers": driver_performance(conn, p), "inspections": insp,
        }


# ---------- CSV export ----------
EXPORT_COLS = {
    "income": ["date", "source", "amount", "driver_name", "truck_number", "notes"],
    "expenses": ["date", "category_name", "description", "amount", "driver_name", "truck_number"],
    "fuel": ["date", "truck_number", "driver_name", "gallons", "price_per_gallon", "total", "miles", "mpg", "location"],
    "loads": ["due_date", "delivered_date", "origin", "destination", "cargo", "driver_name", "truck_number", "miles", "pay", "status"],
    "inspections": ["date", "result", "driver_name", "truck_number", "location", "fine_amount", "fine_reason", "notes"],
}


@secure.get("/export/{table}")
def export_csv(table: str, p=Depends(period)):
    if table not in EXPORT_COLS:
        raise HTTPException(404, "Unknown table")
    col = "COALESCE(x.delivered_date, x.due_date)" if table == "loads" else "x.date"
    with get_conn() as conn:
        data = list_table(conn, table, f"WHERE {rng(col)}", p)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=EXPORT_COLS[table], extrasaction="ignore")
    w.writeheader()
    w.writerows(data)
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="mccoy-{table}.csv"'})


# ---------- Users ----------
class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6)


@secure.get("/users")
def list_users():
    with get_conn() as conn:
        return rows(conn, "SELECT id, username, created_at FROM users ORDER BY id")


@secure.post("/users")
def create_user(body: UserIn):
    username = body.username.strip().lower()
    with get_conn() as conn:
        if one(conn, "SELECT id FROM users WHERE username = ?", (username,)):
            raise HTTPException(400, "That username is already taken")
        uid = conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                           (username, hash_password(body.password))).lastrowid
        return one(conn, "SELECT id, username, created_at FROM users WHERE id = ?", (uid,))


@secure.delete("/users/{uid}")
def delete_user(uid: int, user=Depends(get_current_user)):
    if uid == user["id"]:
        raise HTTPException(400, "You can't remove your own account")
    with get_conn() as conn:
        target = one(conn, "SELECT id, username FROM users WHERE id = ?", (uid,))
        if not target:
            raise HTTPException(404, "Not found")
        if target["username"] == os.environ["OWNER_USERNAME"].lower():
            raise HTTPException(400, "The owner account can't be removed")
        conn.execute("DELETE FROM users WHERE id = ?", (uid,))
    return {"ok": True}


# ---------- Test data ----------
@secure.get("/test-data")
def test_data_get():
    return test_data_status()


@secure.post("/test-data")
def test_data_add():
    clear_test_data()
    seed_test_data()
    return test_data_status()


@secure.delete("/test-data")
def test_data_remove():
    return {"removed": clear_test_data()}


app.include_router(api)
app.include_router(secure)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ["CORS_ORIGINS"].split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    seed_owner()
