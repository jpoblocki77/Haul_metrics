# HaulMetrics – Virtual Trucking Company Tracker
## Problem statement
Python app with SQLite storage for a virtual trucking company: income, expenses (custom categories), charts, add/remove test data, trucks (number + tank gallons, used to fill in fuel gallons), fuel (gallons, $/gal, auto total, MPG, avg MPG, gallons bought), loads On Time/Late, driver performance, DOT inspections (Passed/Fined/Out of Service, fine reason).
## Architecture
FastAPI + sqlite3 (backend/fleet.db; db.py, auth.py, seed.py, server.py). React + shadcn + recharts frontend. JWT bearer auth, owner account seeded from .env.
## Implemented (Jun 2026)
- Owner login, dashboard with KPIs and 7 charts
- CRUD for income, expenses, categories, trucks, drivers, fuel, loads, inspections
- Fuel gallons auto-filled from the truck's tank size, total and MPG worked out on the backend
- Loads create, update and delete their linked income automatically
- Driver/truck performance stats, fines by reason
- Sample data tagged is_test: add/remove from UI
## Backlog
- P1: Desktop window wrapper (pywebview), CSV export, date range filters
- P2: Brute-force login lockout, multiple users/roles, shadcn date picker
