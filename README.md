# McCoy Trucking

Virtual trucking company tracker: income, expenses, fuel and MPG, loads, drivers, DOT inspections. Built with Python (FastAPI) and SQLite.

## Run as a desktop app (Windows / macOS / Linux)

You need Python 3.10+ and Node.js with yarn.

```bash
# 1. Build the screens once (leave the backend URL empty so it uses the local server)
cd frontend
yarn install
REACT_APP_BACKEND_URL= yarn build        # Windows PowerShell: $env:REACT_APP_BACKEND_URL=""; yarn build

# 2. Install Python packages and start the app
cd ../backend
pip install -r requirements-desktop.txt
python desktop.py
```

A "McCoy Trucking" window opens. Sign in with `owner` / `trucker123`. You can change this by setting the
`OWNER_USERNAME` / `OWNER_PASSWORD` environment variables, or by adding users on the Users page.
All data is saved in `backend/fleet.db` (SQLite). Back up that file to keep your records safe.
