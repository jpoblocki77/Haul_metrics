# McCoy Trucking — Virtual Trucking Company Manager

## Original problem statement
"Make me an app for tracking income expendatrues and driver performace of a virtual trucking company add graphs and charts and the ability to add expense catogories add the ability to add and remove test data use sqlite as data storage make this a python app that uses sqlite for data storage add tracking for fuel mpg average mpg gallons bought Price per gal;lon and auto calculate fuel purchase total add the ability to add trucks by truck number and how many gallons they hold use how many gallons are held by a truck thru its truck number and use it in the fuel calulation add the ability to check if a load was on time or late also add a dot inspection records with the ablity to check if passed, fined, or put out of service add a fines reason field so i can track what fines were for"

## Architecture / invariants
- Existing FastAPI + SQLite app retained, as explicitly requested originally. React + shadcn + Recharts frontend. Python pywebview Windows desktop packaging.
- Backend: server.py dynamic CRUD/stats; db.py schema and automatically closed connections; auth.py bcrypt/PyJWT; seed.py realistic tagged test data.
- Additional backend modules: telemetry.py, telemetry_engine.py, telemetry_bridge.py, backups.py, company.py, profiles.py.
- Frontend uses REACT_APP_BACKEND_URL; all backend routes /api. SQLite path configured in existing backend environment. Keep original protected environment keys.
- Accounts: owners full access; dispatchers add/edit operational records, never delete, manage accounts, change company settings, reset records, or backup/restore.
- Signing out revokes only that JWT; each sign-in gets a unique jti. Role/password changes revoke that user's sessions. Restore revokes all sessions. Persistent account + client-address login lockout. Owner seeding is creation-only.
- test_credentials.md is source of current test credentials; no permanent credentials changed in this work.

## Approved choices
- Telemetry: **Review before saving**. Detected loads/fuel stops are candidates, not automatically booked.
- User creation: owner manually enters password, with confirmation; default role Dispatcher.
- Company colors: main, accent, separate dark/light backgrounds. Settings owner-only, company-wide.
- Erase all records: **Keep accounts and company settings**. Never erase users or branding in that action.

## Completed functionality
### Core (prior iterations)
- Income/expenses/categories/trucks/drivers/loads/fuel/inspections CRUD; driver/truck performance; tank capacity auto-fill, purchase totals and MPG; on-time/late and inspection result/fine reason.
- Linked load income automatically created/updated/deleted. Date filters, CSV exports, dashboard with seven charts, tagged test-data add/remove.
- Monthly rankings, historical Top Driver winners/trophy counts. Desktop window; Windows executable packaging scripts/GitHub workflow configured.

### Additions and fixes (2026-10-28 through 2026-10-29)
- `/users/new`: simple username/password/confirmation/role form, password visibility, validation and clear success. `/users`: edit role/reset password/remove users; self-demotion guarded.
- Persistent dark/light toggle on login/sidebar. `/company`: editable name, main/accent/dark/light colors, readable background validation, previews, persistence. Login/header/report/browser title follow saved name; charts and theme surfaces follow colors.
- Today range uses local browser calendar day. Existing week/month/custom/all filters retained.
- `/drivers/:id`: filtered performance/loads/fuel/inspections, MPG trend, all-time trophy cabinet. Long names and mobile leaderboard winner layout verified.
- `/report`: daily income/expenses (including fuel and fines) and weighted MPG charts; company totals; top-five driver summary to keep printed report one page. Actual chart pixels and PDF verified, not just SVG existence.
- `/telemetry`: Funbit SCS HTTP protocol, persisted account-to-driver/truck mapping, review/dismiss/history. Conservative stationary refueling detection, liters/km conversions, full-to-full MPG only. Pauses/disconnects/odometer resets invalidate incomplete observations. New identical jobs are recognized after the prior job becomes empty; mere trailer detachment never marks delivery.
- Load approval atomically creates load + linked income once; fuel requires actual price. Repeated review rejected. Dispatchers see only their own detections; owners all.
- Downloadable bridge and Windows launcher. Fixed crash caused by public HTTP/proxy URL, default urllib User-Agent being rejected, and unhandled startup errors. Public origin comes from configured frontend URL, never proxy Host. Honest app User-Agent; local password prompt, retries, visible errors, private error-type log. Real downloaded/source bridge authentication tested repeatedly.
- `/backup`: encrypted portable .mccoy (scrypt/Fernet), preview counts, current-owner password and typed RESTORE MCCOY confirmation, schema/date/FK/envelope validation, atomic restore. Includes account hashes, all company data, branding, telemetry history. Device baselines/connections reset; no signing secret included. Backup files downloaded directly; no external object storage.
- Global **Delete entries** utility on every protected page, owner-only, all ten record types incl accounts/telemetry, search, separate cancel/confirmation per entry. Direct delete controls in profiles and telemetry, existing CRUD row deletes retained. All affected displays refresh without manual reload.
- Telemetry management has server-side pagination/search/true total; full live history no longer silently capped at 500. Searches decoded historical/restored JSON scalar values with Unicode casefold and literal `%`, `_`, backslash handling. Verified 501-event pagination/oldest deletion.
- **Backup & Restore → Erase company records**: exact ERASE ALL RECORDS phrase + current owner password, atomic clearing of company records, categories and telemetry history/connections. Accounts, branding and security metadata preserved. IDs not reused. Categories seed only on first installation and do not return after intentional erasure.
- Extra reliability fixes: manual ISO calendar-date validation, malformed backup metadata returns controlled errors, CSV formula-leading strings escaped, DB connections closed deterministically, SQLite telemetry work kept off async event loop.

## Key endpoints
- `/api/auth/login`, `/me`, `/logout`; `/api/users`, PATCH/DELETE `/api/users/{id}`.
- `/api/{income,expenses,fuel,loads,drivers,trucks,inspections,categories}`; dashboard/leaderboard/history/report-charts stats; `/api/drivers/{id}/profile`.
- `/api/company/branding` GET public appearance only / PUT owner; `/record-counts` GET owner; `/erase-records` POST owner.
- `/api/telemetry/status`, `/settings`, `/ingest`, `/local-poll` desktop only, `/bridge`, `/launcher`, `/events`, `/manage-events` owner paginated, `/events/{id}/review`, DELETE `/events/{id}` owner.
- `/api/backup/export`, `/inspect`, `/restore` owner-only.

## Verification and data safety
- Production frontend build and Python compile passed. Reports iteration_4 through iteration_7 document findings/fixes.
- Original 31 serial API regression tests passed in iterations 5/6. Five extra telemetry management tests initially uncovered two related encoding failures; iteration 7 verified all **5/5**, closing both.
- Final pre-completion check flagged only fixture-import lint conflicts in generated tests. Moved shared fixture discovery to backend/tests/conftest.py without changing product behavior. Ruff F811 check passed; **all 36 API tests then ran together with explicit pytest -n0 and passed** (103.51s). Final JUnit: `/app/test_reports/pytest/pytest_results_final_complete.xml`. Safeguarded suite teardowns restored and compared original company data.
- Full route/theme/mobile matrix, all CRUD/user/backup/erase flows, ten global delete types, 19 focused winner/pagination/direct-delete/mobile-refresh groups passed.
- Report charts visibly rendered at desktop/mobile and in a rasterized one-page printed PDF.
- Actual downloaded and source bridge subprocesses authenticated to the real external API and remained polling until intentionally stopped by test harness.
- Final Unicode/casefold/literal-symbol search confirmed by independent API/browser checks before and after encrypted restore. Latest report: `/app/test_reports/iteration_7.json`, no remaining runnable defect reported.
- Original company records, account password hashes and branding safeguarded/restored/compared repeatedly. No retained temporary accounts/data. Existing accounts/credentials unchanged; test restore intentionally revokes sessions and IDs may advance.
- IMPORTANT tests share a live preview database: **always explicit `pytest -n0`**, foreground, one safeguarded suite at a time. Default repository pytest configuration is parallel and must not be used for these suites. Never run unsafeguarded destructive tests on original data.
- Product APIs are real, not mocked. SCS inputs in automated tests are SIMULATED. Pre-existing bridge contract tests mock input/network fixtures, separately from real bridge authentication verification.

## Limitations and roadmap
- **Functional P0: none known** after final search verification; all runnable requested flows covered. Functional test success is not security clearance.
- **Security audit (2026-10-29): ACTION REQUIRED.** Read-only audit found HIGH SEC-001: workspace CORS_ORIGINS=* + credentialed CORS + SameSite=None cookie can permit cross-site authenticated access. Production values not verified. LOW SEC-002: login timing enumeration/targeted account lockout. Additional hardening: default desktop owner credential and browser JWT localStorage. No security remediation applied yet; user requested audit only. See `/app/memory/SECURITY_AUDIT.md`. Prioritize CORS/CSRF remediation and regression tests before treating app as security-cleared.
- **P1: user-PC verification** of actual Windows BAT/EXE launch and real SCS/Funbit game capture. Linux preview cannot verify these. Installer workflow is configured, but no Windows executable built or run here.
- SCS snapshots do not provide reliable delivered/cancelled events or fuel prices. Those remain explicit review fields. Simulator deadlines are not real dates; ETS2 currency is not automatically converted to USD. Connection gaps may miss partial fuel stops; use manual entry where necessary.
- Cloud usage requires freshly downloaded McCoyTelemetry.py + StartMcCoyTelemetry.bat together on driving PC with Python 3.10+ and Funbit server/plugin running. Never expose telemetry port publicly.
- P2: code-signed installer, native gameplay-event integration, optional deletion/activity audit log.