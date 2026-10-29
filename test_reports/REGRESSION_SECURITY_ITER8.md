# Full functional and security regression — iteration 8

## Verdict
**ACTION REQUIRED.** Core operational functionality and revised erase preservation work. A new authenticated data-validation defect can persist infinite financial values and break lists/dashboards. The public preview boundary does not preserve the application's advertised SameSite/CORS response policy. No successful cross-origin authenticated read/write bypass was observed.

This run was **preview only**. No production checks, deployment, product edits, password changes, or permanently retained company changes were performed. Functional success is not security clearance.

## Executed results (not historical claims)
| Scope | Result | Notes |
|---|---:|---|
| Existing six-suite serial API regression | 35/36 | Only failure: public cookie not SameSite=Lax. All CRUD, relational income, totals, reports, roles, backups, persistence, erase and501-history tests passed. |
| New public security pytest | 7/19 initially | Ten strict hostile-response header assertions fail on added wildcard ACAO; cookie contract fails; one cache equality assertion was too strict. |
| Corrected cache directive/auth-login assertion | 1/1 rerun | `no-store, no-cache, must-revalidate` correctly includes no-store. This was a harness false positive, not a cache vulnerability. |
| Disposable security pytest final | 4/7 | Fail-closed config, desktop origin, spoofed Host/cookie/logout, SQL text/private hashes pass. NaN/±Infinity validation cases fail. |
| Full browser workflow | 24/26 groups | Rapid matrix report429; old mobile candidate setup failed before review. Raw failures retained. |
| Global/direct delete and erase browser regression | 7/7 groups | All10 delete types, cancel/confirm, direct profile/telemetry delete, mobile refresh, role restrictions and erase. |
| Focused photos/logout/CSRF/erase/roles/iframe | 16/16 groups | Includes64 owner route/theme/size combinations and44 dispatcher combinations. |
| Independent mobile telemetry dialog | 2/2 | Dark/light, fits390px, inputs/select usable, cancel leaves candidate pending and loads unchanged. Closes old harness setup coverage gap. |
| Mobile sign-in visual | 1/1 | No overflow, theme switch works; image loads but intentionally hidden. |
| Actual downloaded + source bridge startup | 2/2 | Real preview network, bearer authentication, no Origin/CSRF headers; intentionally stopped after polling started. No real game available. |
| Build / Python compile | Passed | `yarn build`; `python -m compileall -q /app/backend`. |

Do not sum retries as new features. Latest three main browser suites plus targeted review total49/51 recorded groups, with a separate visual check. Security public raw JUnit remains7/19; a single corrected assertion passed afterward, not a newly executed19/19 run.

## Findings and reproduction

### HIGH — persistent non-finite financial data poisoning
Disposable database, authenticated owner session:

```text
POST /api/income
{date: valid ISO date, source: TEST_nonfinite, amount: "Infinity"}
=>500; row persists with SQLite amount=inf
GET /api/income =>500
GET /api/stats/dashboard =>500
```

`"-Infinity"` behaves the same. `"NaN"` returns400 `Invalid reference to another record` and persists nothing.

**Root cause:** plain Pydantic floats permit non-finite coercion. `run()` commits the transaction before JSON serialization, which rejects infinity. NaN becomes NULL in SQLite and triggers a misleading integrity-error response. The authenticated operational endpoints do not add owner-only checks for normal writes, so review all comparable float models rather than fixing income alone. This class was reproduced against actual application code in an isolated DB; no poison payload went to live preview.

**Recommended next action:** reject non-finite values at model validation before writes; add reusable coverage across income/expenses/fuel/loads/inspections/trucks; safely assess existing data without deleting legitimate rows. Keep400/422 errors meaningful.

### Preview boundary — cookie/CORS configuration drift
Sanitized evidence: `security_boundary_iter8.json`.

| Response | Isolated app | Public preview |
|---|---|---|
| Login cookie | HttpOnly;Secure;SameSite=Lax | HttpOnly;Secure;SameSite=None;Partitioned |
| Untrusted actual API |403, no ACAO/ACAC |403, ACAO:* but **no ACAC** |
| Untrusted preflight |400, no ACAO/ACAC |400, no ACAO/ACAC |
| Trusted actual API |Exact app ACAO;ACAC:true |Exact app ACAO;ACAC:true |
| Cache-Control |no-store |no-store,no-cache,must-revalidate |

Ten hostile origins covered null, arbitrary external domain, sibling subdomain, suffix lookalike, alternate scheme/port, malformed origin/path/brackets and credential-bearing origin. Actual writes reject before handlers. Forwarded-host manipulations do not change the trusted origin. Independent isolated Host spoofing also passes. These tests demonstrate application guards working, **not** production correctness. Wildcard ACAO without credentials plus403 is not proof of the original credentialed-CORS exploit; the strict public policy/cookie contract nonetheless differs from source and documentation.

Investigate preview ingress/header-cookie rewriting. Do not remove CSRF or weaken origin validation to make embedded contexts pass. Actual production verification remains a separate read-only next step.

### Transient preview429 during rapid full-page navigation
One report matrix step showed a429 alert, disabled print button and loading report placeholder. Other populated report checks produced a genuine one-page PDF with charts. Slower SPA owner/dispatcher route matrices completed without429. There is no report limiter in reviewed backend source; an upstream/client-edge limiter is suspected, exact layer not proven. Retain raw failure and investigate/retry rather than declaring a flawless run.

### Existing security risks remain
- Original LOW SEC-002: unknown-user login skips bcrypt; account-wide five-failure lockout enables timing enumeration/targeted temporary denial of access. Still present in source, not newly stress-tested against original accounts.
- Known initial desktop credentials remain in the bootstrap/documentation; first-run change/setup hardening remains outstanding. Credentials are deliberately omitted here.
- Production origin, secret strength, TLS termination, Windows executable and real gameplay cannot be certified from this environment.

## Verified browser security and UI behavior
- HttpOnly/Secure session not readable from `document.cookie`; no persistent browser bearer in localStorage; legacy key removed; reload works.
- Missing/wrong/non-ASCII/another-session/stale CSRF tokens reject before writes; invalid bearer cannot fall back to valid cookie.
- Real CSRF retry test changed only the first outbound POST header: real middleware returned403; frontend fetched token and retried exactly once; exactly one income row persisted.
- Real logout revokes copied browser token, signs sibling tabs out via nonsecret event, and leaves separately logged-in browser context/bridge token valid.
- **MOCKED** logout503 and network abort validate visible error, busy disabled control, retained signed-in state and successful retry. Already-revoked401 is treated as signed out. Delayed actual `/me` response cannot undo the client logout event.
- Header logout present on all protected pages. Desktop and mobile sidebar logout controls are independently visible/clickable.
- Local dashboard images have naturalWidth>0, meaningful truck framing and alt descriptions at1920×800/390×844 in dark/light; no horizontal overflow. Desktop highway sign-in photo clear. Mobile sign-in loads the local image but hides its container by design; clarify if mobile sign-in photography is required.
- External parent HTML is **MOCKED**, child is actual preview. A fresh embedded login/reload works with preview partitioned cookies. Existing top-level session is not shared into that partition. Production Lax third-party behavior remains unverified.

## Erase preservation and original-data safety
The new contract is enforced by tests, not relaxed:

**Erased only:** telemetry_events,income,expenses,fuel,inspections,loads.

**Exact preserved:** users,company_settings,categories,drivers,trucks,telemetry_sources — all columns, IDs, notes/tank values, tagged/default/custom categories, assignments, enabled flags, raw source state,last_seen. Compared before any post-erase sample arrives.

- API bearer erase and actual UI cookie+CSRF erase passed. Invalid phrase/password/missing fields/dispatcher/missing or bad CSRF do not change records.
- Preview counts enumerate only six activity tables; UI warning/dialog describe preserved setup. Cancel and wrong password safe; current sessions remain valid; historical stats reset.
- Active erased job does not immediately resurrect; NEXT snapshot accepted; after empty job a genuinely new job and new fuel stop produce candidates.
- Preserved driver profile200 with zero loads; preserved truck tank123 re-used through actual fuel form and MPG6 computed correctly; categories remain usable. Separate owner deletion still works.
- Backup restore remains deliberately different: transferred source state is disabled/reset and sessions revoked; existing restore regressions pass.

Every mutating command ran inside a private SQLite online-backup guard and compared **every table** afterward, including accounts/session versions, login attempts, revocations and sqlite_sequence. Encrypted archives alone cannot safeguard active sources because export normalizes them; exact SQLite guard covers that gap. Original current state was read, not assumed empty. At start/end: users2,categories8,default branding(settings0),activity/fleet/source0,login_attempts3,revocations35. Sources were explicitly seeded active with state/last_seen for erase proofs. Temporary rows/accounts removed by exact restore; original credentials independently reverified. Private plaintext snapshots use0700 directory/0600 file and are removed on exit. Retained encrypted recovery archives use0600. SQLite physical bytes may differ despite exact logical row restoration.

No product edits by this tester. Pre-existing product diffs belong to implementation; only test scripts/reports were changed. No permanent company/account/password/connection changes.

## Repeatable commands
The wrapper loads existing env files, snapshots the actual current database privately, runs one foreground command, and restores/compares exact rows even on failures. **Never run live suites with repository-default parallel pytest. Never run two guarded commands concurrently.**

```bash
cd /app/backend
python tests/run_guarded_regression.py pytest -n0 \
  tests/test_full_regression.py tests/test_latest_features.py \
  tests/test_final_verification.py tests/test_isolated_persistence.py \
  tests/test_delete_erase_regression.py tests/test_telemetry_management.py \
  -v --tb=short --junitxml=/app/test_reports/pytest/pytest_results_functional_retest.xml

python tests/run_guarded_regression.py pytest -n0 \
  tests/test_browser_security_regression.py -v --tb=short \
  --junitxml=/app/test_reports/pytest/pytest_results_security_retest.xml

python tests/run_guarded_regression.py pytest -n0 \
  tests/test_isolated_browser_security.py -v -s --tb=short \
  --junitxml=/app/test_reports/pytest/pytest_results_isolated_security_retest.xml

python tests/run_guarded_regression.py python tests/ui_security_preservation.py
python tests/run_guarded_regression.py python tests/ui_delete_erase_regression.py
python tests/run_guarded_regression.py python tests/check_mobile_telemetry_dialog.py
python tests/run_guarded_regression.py python tests/check_bridge_real_startup.py
python tests/run_guarded_regression.py python tests/check_security_boundary.py
python tests/run_guarded_regression.py python tests/check_iter8_closeout.py
```

Use maintenance coordination for future live-company tests: exact restore necessarily rolls back concurrent writes made during a safeguarded test window. Prefer disposable DB for destructive hostile-input tests. No concurrent original-company telemetry source was present in this run. Shared `ctx` remains discovered through conftest; test modules do not import it.

## Artifacts
Machine-readable report: `/app/test_reports/iteration_8.json`; JUnit and browser paths listed there. Sanitized runtime comparison: `security_boundary_iter8.json`. Closeout credential/row summary: `closeout_iter8.json`; final persisted guard proof: `preservation_iter8.json`. Earlier command preservation confirmations are tool logs; persistence of the guard proof file was added at final closeout, not retroactively fabricated.

No product API MOCKED outside deliberate browser logout error injection. Existing bridge contract harness MOCKS input/network separately; real network bridge startup also verified. SCS sample data **SIMULATED**, not a real game.