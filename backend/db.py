import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / os.environ["SQLITE_DB_FILE"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  is_test INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS trucks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  truck_number TEXT UNIQUE NOT NULL,
  tank_gallons REAL NOT NULL,
  make_model TEXT,
  is_test INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS drivers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  notes TEXT,
  is_test INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS loads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  origin TEXT NOT NULL,
  destination TEXT NOT NULL,
  cargo TEXT,
  driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
  truck_id INTEGER REFERENCES trucks(id) ON DELETE SET NULL,
  pay REAL NOT NULL DEFAULT 0,
  miles REAL,
  due_date TEXT,
  delivered_date TEXT,
  status TEXT NOT NULL DEFAULT 'On Time',
  is_test INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS income (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  amount REAL NOT NULL,
  source TEXT NOT NULL,
  driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
  truck_id INTEGER REFERENCES trucks(id) ON DELETE SET NULL,
  load_id INTEGER REFERENCES loads(id) ON DELETE CASCADE,
  notes TEXT,
  is_test INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  amount REAL NOT NULL,
  category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
  truck_id INTEGER REFERENCES trucks(id) ON DELETE SET NULL,
  description TEXT,
  is_test INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS fuel (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  truck_id INTEGER REFERENCES trucks(id) ON DELETE SET NULL,
  driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
  gallons REAL NOT NULL,
  price_per_gallon REAL NOT NULL,
  total REAL NOT NULL,
  miles REAL,
  mpg REAL,
  location TEXT,
  is_test INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS inspections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
  truck_id INTEGER REFERENCES trucks(id) ON DELETE SET NULL,
  location TEXT,
  result TEXT NOT NULL,
  fine_amount REAL,
  fine_reason TEXT,
  notes TEXT,
  is_test INTEGER DEFAULT 0
);
"""

DEFAULT_CATEGORIES = ["Repairs", "Tolls", "Insurance", "Driver Pay", "Tires", "Permits"]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def rows(conn, sql, params=()):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def one(conn, sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return dict(r) if r else None


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        if not one(conn, "SELECT id FROM categories LIMIT 1"):
            conn.executemany("INSERT INTO categories (name) VALUES (?)", [(c,) for c in DEFAULT_CATEGORIES])
