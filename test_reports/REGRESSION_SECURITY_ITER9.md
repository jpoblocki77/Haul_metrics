# Post-fix security and regression closeout — iteration 9

## Verdict: BLOCKED by a new positive-minimum regression
The original NaN/Infinity persistence defect is fixed across the tested create/update fields. However, the fix overrides required-field positive minima: `TruckIn.tank_gallons` and `FuelIn.price_per_gallon` now accept zero, negatives and `1e-320`. Do not claim final verification or production security clearance.

No product code was edited. All mutating commands ran **foreground**, sequentially, through the existing exact SQLite guard; pytest explicitly used `-n0`.

## Newly executed results
| Scope | Result | Detail |
|---|---:|---|
| Existing six-suite functional regression | **32/36** | Truck zero accepted; three subsequent backup groups fail because that accepted row makes an exported archive invalid. Raw failures retained. |
| Disposable numeric/backup final suite | **26/30** | Four create/update tiny-positive truck/price cases fail. All 144 string/raw NaN/±Infinity, giant-exponent and huge-finite attack requests across nine fields reject422. Gallons minimum and negative mileage checks pass. |
| Public browser security | **19/19** | Hostile actual403 before mutation, no credential grant, preflight400, CSRF binding, logout isolation and bearer bridge compatibility. Public assertions explicitly distinguish preview ingress drift from source policy. |
| Strict isolated source security | **7/7** | Strict login/logout Lax, exact allowlist, all ten hostile origins/preflights without ACAO/ACAC, fail-closed configuration and nonfinite income rejection. |
| Separate disposable minimum RCA | **0/1** | Six tank/price tiny/zero/negative create requests return200; zero-tank default fuel returns500; self-export inspect returns400. |
| Paced SPA report browser flow | **4/4** | Real login, income→fuel→dashboard→report, populated charts, actual one-page PDF, logout. No429, page errors or visible errors. |
| Public login smoke | **1/1** | Frontend loads; local desktop photograph visible. |
| Actual downloaded/source bridge startup | **2/2** | Real preview authentication; terminated intentionally after entering polling. No Windows/gameplay claim. |
| Read-only original REAL audit | **0 nonfinite** | 13 REAL columns assessed; no company values retained in report and no repair/deletion performed. |
| Python compile / frontend build | **Passed** | Final compileall; yarn production build compiled successfully. |
| Ruff | **Not clean** | Product server.py/backups.py:51 findings (29 UP045,14 B008,4 I001,2 TRY004,1 SIM102,1 UP017). Separate F811 check passed. No product lint auto-fixes. |

Latest pytest results total84/93 passing, nine recorded failures; retries are not added to totals. Initial numeric run25/30 is retained separately: a duplicate truck name masked one positive-minimum failure and shared disposable state caused a cascading archive failure. Test-only corrections gave unique create names and per-case private DB isolation. The final26/30 still exposes real product failures.

## Root cause and reproduction
`SafeNumber = Annotated[float, Field(allow_inf_nan=False, ge=-1e15, le=1e15)]` is combined with required-field assignment `= Field(ge=0.000001)`. In this installed Pydantic version, merged metadata resolves the required tank/price minimum to **-1e15**, confirmed by `model_json_schema()` and runtime requests. Optional gallons/miles constraints do not show the same failure.

1. Create or update a truck with `tank_gallons=1e-320` →200, not422.
2. Create or update fuel with `price_per_gallon=1e-320` →200, not422.
3. Diagnostic tank/price creates with0 and-1 also return200.
4. Create a zero-capacity truck; fuel request with omitted gallons, positive price and miles60 →500. `prep_fuel` defaults gallons from that zero tank and divides before the derived-value guard.
5. Export these API-accepted records →200; inspect the unmodified export →400 because backups correctly requires tank/price minima. Full regression backup inspect/restore/sample-cleanup groups consequently fail.

**Fix recommendation:** define an unambiguous positive finite bounded type (e.g. one Annotated Field with ge=1e-6/le=1e15/allow_inf_nan=False), avoiding two competing lower bounds; use it on required tank/price and verify generated schema. Preserve negative monetary adjustments and nonnegative miles. Guard invalid stored/default tank quantities before fuel division. Retest the failing numeric cases and all36 functional cases; do not relax assertions or weaken backup validation.

The known metadata merging issue was researched against Pydantic issue11361: https://github.com/pydantic/pydantic/issues/11361. Runtime schema evidence, not search advice alone, establishes this RCA.

## Boundary and security assessment
Fresh sanitized comparison is `security_boundary_iter9.json`. Source emits HttpOnly/Secure/Lax, exact trusted ACAO+ACAC, and no hostile ACAO/ACAC. Public preview emits login SameSite=None+Partitioned and hostile403 ACAO:* **without ACAC**. All ten hostile public actual requests still403 and preflights400 without grants; exact pre/post SQLite snapshots show no mutation. No CSRF or authenticated cross-origin bypass was observed. This is a documented residual external policy difference, **not production clearance**. Earlier iteration8 strict public failures remain untouched.

Persisted account lockout after five failures passed within the functional auth case. bcrypt hash privacy/format and valid finite encrypted roundtrip passed in the disposable suite. Source review confirms in-memory browser CSRF, no stored browser JWT and creation-only seeding; these frontend internals were not exhaustively rerun. Known LOW SEC-002 unknown-user timing enumeration/account-wide lockout denial of service and documented default desktop credentials remain unresolved. No brute-force flood against original accounts was attempted.

The iteration8 rapid-navigation429 failure remains in its raw report. Current normal-paced SPA report flow has no429; therefore no new429 headers/logs exist. This is a successful paced retest, not proof the earlier transient can never recur.

## Exact original-data preservation
Original DB this run was **populated**, unlike iteration8's historical empty activity baseline: users2, categories8, drivers6, trucks6, loads60, income68, expenses40, fuel70, inspections20, settings0, sources0, events0, attempts3, revocations35, sqlite_sequence10.

Every guarded command restored and compared **all15 tables/all columns**, including users' password hashes/roles/IDs/session_version, source raw state/enabled/last_seen, attempts, revocations and sqlite_sequence. `original_audit_iter9.json` and `closeout_iter9.json` have the same complete-row fingerprint; final baseline equality passed after bridge startup. Private online SQLite backups were ephemeral0700 directories/0600 files, not plaintext report files. API recovery archives remain encrypted0600. No permanent test accounts/records/credential/source changes remain. Physical SQLite bytes can change while logical rows match exactly.

Live functional regression unintentionally accepted its existing zero-tank rejection case; the guard restored that test-created row and all original/security data exactly. All nonfinite/extreme poison cases and minimum RCA/fuel500 attacks ran **only in disposable DBs**.

Fresh erase test passes exact preservation of all users/settings/categories/drivers/trucks/source rows, including active source state and last_seen, zeroing only the six activity tables. Post-erase new job/fuel and truck reuse pass. Search501/unicode passes. Current cookie erase negative/CSRF cases pass. Previous UI erase7/7, focused UI16/16, mobile review2/2 and owner64/dispatcher44 route matrices are **historical**, not newly counted. Mobile login hidden photo is intentional, not a defect.

## Coverage limits and next steps
- Fix positive minima/default-fuel500 and rerun numeric plus functional suites before claiming closeout.
- Production deployment/origin/TLS/secrets/ingress not inspected; production policy verification remains separate.
- Real SCS gameplay and Windows launch not available. Bridge auth proof is real public network only.
- This is focused regression/security testing, not exhaustive penetration testing.
- No product API MOCKED in new numeric/report/security/bridge tests. Disposable private DBs are isolation, not mocked APIs. Existing full-suite bridge_process_harness uses **MOCKED** input/network; telemetry snapshots are **SIMULATED** game data.

## Repeatable commands
Run one at a time from `/app/backend`, foreground only, with `REGRESSION_PRESERVATION_REPORT` pointing to a new iteration report:

```bash
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json python tests/run_guarded_regression.py pytest -n0 tests/test_numeric_closeout.py -v -s --tb=short
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json python tests/run_guarded_regression.py pytest -n0 tests/test_numeric_minimum_diagnostic.py -v -s --tb=short
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json python tests/run_guarded_regression.py pytest -n0 tests/test_full_regression.py tests/test_latest_features.py tests/test_final_verification.py tests/test_isolated_persistence.py tests/test_delete_erase_regression.py tests/test_telemetry_management.py -v --tb=short
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json python tests/run_guarded_regression.py pytest -n0 tests/test_browser_security_regression.py tests/test_isolated_browser_security.py -v --tb=short
REGRESSION_PRESERVATION_REPORT=/app/test_reports/preservation_next.json python tests/run_guarded_regression.py python tests/ui_report_closeout.py
```

Never restore sanitized API archives alone over active telemetry sources. Coordinate maintenance: exact guard restore necessarily rolls back concurrent writes; no original active source existed in this run.