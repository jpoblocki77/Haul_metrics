import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / os.environ["SQLITE_DB_FILE"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'dispatcher',
  session_version TEXT NOT NULL DEFAULT '0',
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
CREATE TABLE IF NOT EXISTS company_settings (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  company_name TEXT NOT NULL,
  primary_color TEXT NOT NULL,
  accent_color TEXT NOT NULL,
  dark_background TEXT NOT NULL,
  light_background TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS session_revocations (
  token_hash TEXT PRIMARY KEY,
  expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS login_attempts (
  identifier TEXT PRIMARY KEY,
  username TEXT NOT NULL,
  failures INTEGER NOT NULL,
  locked_until REAL NOT NULL
);
"""

DEFAULT_CATEGORIES = ["Repairs", "Tolls", "Insurance", "Driver Pay", "Tires", "Permits"]

TELEMETRY_SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry_sources (
  user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
  truck_id INTEGER REFERENCES trucks(id) ON DELETE SET NULL,
  server_url TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 0,
  state TEXT NOT NULL DEFAULT '{}',
  last_seen TEXT
);
CREATE TABLE IF NOT EXISTS telemetry_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  event_key TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  detected_at TEXT NOT NULL,
  payload TEXT NOT NULL,
  record_id INTEGER,
  reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);
"""


class ManagedConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def get_conn():
    conn = sqlite3.connect(DB_PATH, factory=ManagedConnection)
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
        first_install = not one(conn, "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
        conn.executescript(SCHEMA)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)")]
        if "role" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'dispatcher'")
        if "session_version" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN session_version TEXT NOT NULL DEFAULT '0'")
        conn.executescript(TELEMETRY_SCHEMA)
        if first_install:
            conn.executemany("INSERT INTO categories (name) VALUES (?)", [(c,) for c in DEFAULT_CATEGORIES])
