# Final Security Evaluation — 2026-10-29

## Verdict: ACTION REQUIRED
Functional and security regression checks pass, and the original CORS/CSRF flaw is remediated. Security clearance is **not** granted: the publicly reachable preview still accepts the documented default owner credential.

## Confirmed remediations
- Exact configured app-origin allowlist; hostile origins/preflights rejected before application actions.
- Session-bound HMAC CSRF for unsafe cookie authentication; pure non-browser bearer bridge supported separately.
- HttpOnly/Secure/SameSite=Lax at the application layer; browser bearer removed from localStorage; no-store API responses.
- Per-token logout revocation, visible retry on server/network failure, cross-tab logout, independent bridge sessions preserved.
- Finite/bounded numeric validation, positive minimum fuel quantities, safe legacy tank fallback, sanitized validation errors and defensive backup bounds. Disposable poisoning tests no longer persist invalid values or cause division/serialization500.
- Latest independent testing: **93/93** fresh API/numeric/security tests and **9/9** targeted browser groups. See iteration_10.json.

## HIGH — Known default owner credential accepted in public preview
- Confirmed by authorized automated preview sign-ins using the documented starter credential (password intentionally omitted here).
- Desktop bootstrap also contains a fixed default owner password in tracked source; owner seeding is creation-only but does not enforce first-run password replacement.
- Someone who knows the default can obtain full owner privileges on this preview, including data access, account changes, export and erase.
- **Next action:** change the owner password using Users → Edit, then implement forced first-run owner setup/password change so new installations never retain a known default. Do not silently rotate credentials or lock out the user during an evaluation.
- Verify after remediation that the old default fails and valid owner/dispatcher/bridge flows still work.

## LOW — Username timing and targeted account lockout
- Login only runs bcrypt for an existing username; account-level five-failure lockout can temporarily deny access to a known account.
- Recommend dummy verification for unknown names, client/global throttling and a safe owner recovery path.
- No authentication bypass was demonstrated for this finding.

## Production inspection result
Read-only deployment diagnostics found **no production deployment for this job**: no live URL, deployed image/build, active run or runtime configuration. Resolution error was `v3 deployment not found`.
- Therefore production CORS, cookie behavior, TLS and actual environment/secret configuration could not be inspected; production is unavailable, not confirmed vulnerable or secure.
- No deployment, production login, data mutation, or secret change was performed.
- The known external URL is preview only. If a separate production app exists elsewhere, its actual target is needed for a separate audit.

## Preview boundary differences
Isolated application responses use SameSite=Lax and no hostile CORS grant. Preview ingress rewrites the cookie to SameSite=None;Partitioned and may add wildcard ACAO to denied403 responses **without Allow-Credentials**. Hostile preflights, reads and writes remain blocked; this is not the original credentialed-CORS vulnerability. Retain the app's strict controls and verify the actual deployment independently when available.

## Correction to an interim audit claim
The interim claim that a JWT signing secret was committed in `backend/.env` is **withdrawn**. `git ls-files` shows the file is not tracked; available Git history contains no commits for it. There is no evidence supporting the claimed source-exposed signing-secret/token-forgery path. A private per-environment signing secret stored in an untracked environment file is normal; its presence alone is not a vulnerability.

## Other limits and housekeeping
- Legacy CORS_ORIGINS=* remains unused; remove stale configuration when safely managing environment settings, not by weakening current controls.
- Actual Windows executable/BAT launch and live SCS gameplay require the driving PC. Bridge real network authentication was separately verified; game snapshots were simulated.
- Dependency advisories and exhaustive penetration testing were not completed. Legacy Ruff modernization advisories are separate from security failures; critical checks and build pass.
- All original15 SQLite tables were restored/compared exactly during guarded tests; no credentials were changed, no test records retained and no originals auto-repaired.