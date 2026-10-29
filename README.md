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
`%APPDATA%\McCoyTrucking\fleet.db`. Use **Backup & Restore** for an encrypted, consistent archive while the app is running.
First sign-in: `owner` / `trucker123`. Add dispatchers on the Users page.
Change the initial password using **Users → Edit account**. Account changes persist across restarts.

Windows may show a "Windows protected your PC" notice the first time, because the program isn't code-signed.
Click **More info**, then **Run anyway**.

## Run from source (any OS)
```bash
cd frontend && yarn install && REACT_APP_BACKEND_URL= yarn build
cd ../backend && pip install -r requirements-desktop.txt && python desktop.py
```

## SCS telemetry: ETS2 and ATS

Supported protocol: **Funbit ETS2 Telemetry Web Server** (`GET /api/ets2/telemetry`). SCS SDK plugins without this HTTP endpoint are not interchangeable.
1. Install [Funbit's server and game plugin](https://github.com/Funbit/ets2-telemetry-server), start `Ets2Telemetry.exe`, then load your game profile.
2. Add your driver and truck in McCoy. Open **Live Telemetry**, choose both, enter your local server URL (normally `http://127.0.0.1:25555/api/ets2/telemetry`), enable detection, and save.
3. **Desktop app:** local sampling runs while McCoy is open, even after navigating to another McCoy page.
4. **Online browser:** install Python 3.10+ on your game PC. Download **local bridge** and **Windows launcher** into the same folder, then double-click `StartMcCoyTelemetry.bat` and sign in with your McCoy account. Keep that console open while driving. The launcher detects Python and keeps error messages visible. No extra Python packages are needed.
5. Review detected loads/fuel stops under **To review**. Confirm or dismiss each one. An approved load creates its income exactly once.

The cloud app cannot see your PC's localhost: the authenticated bridge sends snapshots to McCoy over HTTPS. Do not expose telemetry port 25555 to the internet. Credentials are entered locally and the session token is held only in bridge memory. Restart/sign in again after a password reset or role change.

### Detection limits
- Funbit supplies snapshots, not reliable job-delivered/cancelled events. Loads are candidates only; trailer detachment does **not** mark a delivery. Set the real delivery date/status and actual pay yourself.
- Fuel increases while stationary are debounced into one candidate. Reloading a save may resemble a fuel stop, so review before approval. No purchases or prices are invented.
- Litres/km are converted to US gallons/miles. Fuel station prices are not supplied. Enter USD per US gallon. Miles/MPG are prefilled only between consecutive full-tank observations in an uninterrupted connection; otherwise leave miles blank or enter known actual mileage.
- Simulator deadlines use an in-game calendar, not actual calendar dates. ETS2 currency is not converted to USD; confirm your accounting amount in review.
- Connection gaps/restarts discard incomplete refuel observations rather than invent missing quantities; such stops may need manual entry. Use one bridge per account at a time.
- Local SCS game connection and Windows executable need verification on an actual driving PC; online tests use representative protocol snapshots, not a live game.

## Portable encrypted backups
Owners can download `.mccoy` archives in **Backup & Restore**, protected by a separate password of at least 12 characters. Archives contain all company records, categories, users/password hashes, telemetry history and settings, but no server signing secret or active device session. Encryption uses Fernet with a salted scrypt-derived key. Backups are streamed to your download, not stored by a third-party file service.

On another PC, sign in as an owner, select the archive, enter its backup password, and choose **Preview restore**. The preview shows counts and restored owner usernames. Take a current backup before replacing anything. Confirm using the current owner's password and `RESTORE MCCOY`. Restore replaces records atomically and signs everyone out. Sign in using a username/password from the archive. Re-enable telemetry and select the local connection on the new PC. Lost backup passwords cannot be recovered. Upload limit: 18 MB file / 25 MB encoded request.

## Driver profiles and reports
Click a driver's name in **Drivers** to see loads, fuel records, MPG trend, inspections and all-month trophies. The global date filter applies to performance and records; trophies are explicitly all-time. Monthly reports include daily income/expense and weighted MPG charts, all-company totals, and a top-five driver summary so the printout stays one page.

## Accounts, appearance and Today
Owners can open **Create User** and enter username, password, confirmation, and role (Dispatcher by default). Manage role/password changes from **Users → Edit**. Default first sign-in remains `owner` / `trucker123` only until an owner changes it.

Use the sidebar or sign-in page's theme switch for dark/light mode; your preference stays in this browser. **Company & Colors** lets owners change the company name, main/accent colors, and separate dark/light backgrounds. Background choices are validated for readability; branding is stored with company records and included in backups. Printed reports always have a white paper background with readable company colors. Existing `.mccoy` backups without settings restore the original McCoy branding.

**Today** in the date range bar uses your PC/browser's local calendar date and applies to filtered records, dashboard totals, driver profiles and CSV exports.

### If the telemetry bridge will not stay open
Download fresh copies of **McCoyTelemetry.py** and **StartMcCoyTelemetry.bat**. Keep them together, then use the `.bat` launcher. Public app URLs always use HTTPS even if an upstream proxy reports HTTP. Startup errors stay visible and error types are logged to `%LOCALAPPDATA%\McCoyTrucking\telemetry-bridge.log` (home directory on other systems), without passwords/tokens. Wrong credentials prompt again; unavailable SCS servers retry. Use Python, not pythonw, for the interactive console.

## Delete entries and start fresh
Owners have a **Delete entries** button on every signed-in page. Select a record type, search across all dates, and confirm an individual deletion. Existing row delete buttons remain available; driver profiles and telemetry history now have them too. Deleting a load removes its linked income. Deleting a driver/truck leaves past records unassigned. Deleting a telemetry detection does not delete an already-approved load/fuel entry.

In **Backup & Restore → Erase company records**, owners can permanently remove recorded activity: income, expenses, fuel purchases, loads, inspections and telemetry event history. This keeps **all drivers, trucks, expense categories, user accounts, company settings and telemetry connections** unchanged, including connection assignments, enabled state and live detector state. Download a backup first. Enter your owner password and type `ERASE ALL RECORDS` to authorize. Live telemetry stays connected and can detect new activity. Existing drivers, trucks and categories remain ready for new records; their individual delete controls are still available separately. Dispatchers cannot delete entries or erase the company. (A backup restore is a different operation and still disables transferred telemetry connections for safety.)

## Browser security and logout
Browser access is restricted to the exact app origin configured by `REACT_APP_BACKEND_URL`; the legacy wildcard `CORS_ORIGINS` is no longer used. The desktop launcher supplies its exact local origin separately. Hosted sessions use a Secure, HttpOnly, SameSite=Lax cookie. Unsafe cookie-authenticated requests require a session-bound CSRF header; the app retrieves it after a reload. The local Python bridge continues to use an explicit bearer token without browser cookies.

**Log out** is available at the top of every signed-in page, as well as in the sidebar. It confirms server-side revocation, clears the browser session state, and signs other tabs of the same browser out. Separate bridge logins remain valid. If the server cannot be reached, logout reports the failure and lets you retry rather than claiming the session was revoked.

Three optimized truck photographs are bundled locally for the dashboard; the sign-in photograph is also local, so these assets travel with the desktop build. Sources are listed in `frontend/public/images/trucking/CREDITS.md`.
