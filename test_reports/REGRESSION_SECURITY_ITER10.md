# Independent final positive-quantity verification — iteration 10

## Verdict
**The iteration-9 numeric blocker is independently closed in preview.** Newly executed serial pytest: **93/93**, no failures/skips/retries. Newly executed browser groups: report **4/4**, erase-to-normal-fuel **4/4**, public login smoke **1/1**. No product source edits. This is not production deployment approval or formal security clearance.

| Fresh scope | Actual result |
|---|---:|
| Disposable numeric CRUD/backup suite | 30/30 |
| Minimum diagnostic, enhanced with six legacy-tank fallbacks | 1/1 |
| Existing six functional suites | 36/36 |
| Public attack resistance | 19/19 |
| Strict isolated application security | 7/7 |
| Paced report/charts/one-page PDF/logout | 4/4 |
| Browser erase, preserved-truck normal fuel creation, stats/logout | 4/4 |
| Public login form load/editability | 1/1 |

Generated XML contains exactly 31 numeric, 36 functional and 26 security cases. `execution_counts_iter10.json` independently checks those fresh artifacts. Earlier iteration8/9 failures and historical browser/bridge successes are not added to these totals.

## Numeric proof
- Runtime schemas now set required tank capacity and fuel price minimum to **1e-6**. Tiny/zero/negative create and update quantities reject422, with complete disposable-database no-mutation assertions.
- String/raw NaN/±Infinity, giant exponents and excessive finite inputs reject422 without persistence or secret echoes across nine create/update numeric fields. Negative monetary adjustments persist correctly. Fuel/load miles retain nonnegative bounds.
- Six deliberately stored legacy capacities (zero, negative, tiny, excessive finite, ±Infinity) were injected **only into a disposable DB**. Omitted-gallons fuel requests all return422, not500, with no additional mutation. They are discarded at fixture teardown; no live poison records were created.
- API-valid positive records export, inspect and restore successfully. Invalid encrypted archives reject400 atomically. Finite derived values and normal fuel computations remain correct.
- Real cookie-authenticated browser erase clears only six activity tables; all six setup/account/source tables match exactly immediately afterward. Preserved truck selection autofills its tank capacity; normal fuel preview, POST, persisted row and refreshed stats pass.

## Preservation
Every mutating command was a foreground child of `run_guarded_regression.py`; pytest explicitly used `-n0`. No overlapping live-database test commands or concurrent original source were present. Private SQLite snapshots used ephemeral0700 directories and0600 files, then were removed. API safety archives remain encrypted0600.

The **populated** baseline and final state match every row/all columns in all15 tables, not merely counts or a sanitized archive: users2, categories8, drivers6, trucks6, loads60, income68, expenses40, fuel70, inspections20, settings0, sources0, events0, login_attempts3, revocations35, sqlite_sequence10. This includes password hashes, roles, session versions, security metadata, raw source state and sequences. Final complete-row fingerprint matches the fresh read-only baseline. Audit of13 REAL columns finds **0 nonfinite and0 invalid** values. No original repair or deletion was performed; no test records remain.

Portable backups intentionally sanitize source state, so archive restoration is not accepted as proof of original-data preservation. Future safeguards require maintenance coordination because exact restoration rolls back concurrent writes.

## Remaining issues and limits
- Fresh boundary comparison still shows source HttpOnly/Secure/**Lax** versus preview login **None+Partitioned**. Hostile public actual requests remain403 with ingress-added ACAO:* **without ACAC**; all hostile preflights400 without an origin/credential grant. Strict source allowlist/CSRF assertions remain intact. Resolve/verify the actual production boundary separately; do not weaken guards.
- Known source-reviewed SEC-002 username timing difference and account-wide temporary lockout denial-of-service risk remain. Existing default desktop credential hardening remains a separate audit item. No new exploitation or production compromise claimed.
- Historical iteration8 rapid-navigation429 is retained. Both fresh normal-paced browser flows have no429, page errors or visible errors; this is not proof recurrence is impossible.
- Python compileall and product critical Ruff checks `E9,F63,F7,F82,F811` pass. `yarn build` compiles successfully. Full advisory Ruff cleanup was not rerun or claimed; iteration9's51 legacy/style findings remain advisory follow-up.
- Actual production configuration/TLS/secrets/ingress and formal `security_audit_agent` review are still required. Full unchanged UI matrices were not rerun. Real Windows BAT/EXE launch and SCS gameplay remain unavailable. Actual bridge startup2/2 is historical iteration9 evidence, not a fresh result.

**Mocking disclosure:** no new product API or browser flow MOCKED. Disposable FastAPI TestClient requests execute the real application. Existing bridge contract harness uses **MOCKED input/network**; functional telemetry/game samples are **SIMULATED**, not live gameplay.

## Fresh-run pattern
From `/app/backend`, foreground, one command at a time:

```bash
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json NUMERIC_DIAGNOSTIC_REPORT=/app/test_reports/numeric_minimum_next.json python tests/run_guarded_regression.py pytest -n0 tests/test_numeric_closeout.py tests/test_numeric_minimum_diagnostic.py -v --tb=short
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json python tests/run_guarded_regression.py pytest -n0 tests/test_full_regression.py tests/test_latest_features.py tests/test_final_verification.py tests/test_isolated_persistence.py tests/test_delete_erase_regression.py tests/test_telemetry_management.py -v --tb=short
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json python tests/run_guarded_regression.py pytest -n0 tests/test_browser_security_regression.py tests/test_isolated_browser_security.py -v --tb=short
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json REPORT_BROWSER_OUTPUT=/app/test_reports/browser_next_report python tests/run_guarded_regression.py python tests/ui_report_closeout.py
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json FUEL_BROWSER_OUTPUT=/app/test_reports/browser_next_fuel python tests/run_guarded_regression.py python tests/ui_fuel_after_erase_closeout.py
```