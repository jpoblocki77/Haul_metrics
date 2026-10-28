# McCoy Trucking

Virtual trucking company tracker: income, expenses, fuel and MPG, loads, drivers, leaderboard, DOT inspections and monthly reports. Built with Python (FastAPI) and SQLite.

## Get the one-click Windows program (McCoyTrucking.exe)

**Option A: let GitHub build it (no installs on your PC)**
1. Push this project to GitHub (use "Save to GitHub" in Emergent).
2. On GitHub, open **Actions**, then **Build Windows app**, then **Run workflow**.
3. When the run finishes (about 5 minutes), download **McCoyTrucking-Windows** from the run page and unzip it.
4. Double-click `McCoyTrucking.exe`. You can pin it to your taskbar.

**Option B: build it on your own Windows PC**
Install Python 3.11+ and Node.js once, then double-click `scripts\build_windows.bat`.
The program appears at `backend\dist\McCoyTrucking.exe`.

### Where your data lives
`%APPDATA%\McCoyTrucking\fleet.db`. Back up this one file to keep all your records.
First sign-in: `owner` / `trucker123`. Add dispatchers on the Users page.

Windows may show a "Windows protected your PC" notice the first time, because the program isn't code-signed.
Click **More info**, then **Run anyway**.

## Run from source (any OS)
```bash
cd frontend && yarn install && REACT_APP_BACKEND_URL= yarn build
cd ../backend && pip install -r requirements-desktop.txt && python desktop.py
```
