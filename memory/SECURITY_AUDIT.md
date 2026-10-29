# Security Audit — 2026-10-29

## Request and scope
User requested: "Run the Security Audit on the deployed app."
Read-only security audit completed against application source and available workspace/preview configuration. No application code was changed, no data mutated, no exploit attempted, and nothing deployed.
**Production runtime was not verified:** the known REACT_APP_BACKEND_URL is a preview URL. Production CORS, cookies, TLS and secrets remain unverified. Findings below are not proof of a production compromise.

## Verdict: ACTION REQUIRED

### SEC-001 — HIGH: overly permissive credentialed CORS
- Evidence: backend/server.py CORS uses CORS_ORIGINS; workspace value is `*`, with allow_credentials=True. Login cookie uses SameSite=None and Secure. auth.py accepts cookie-only authentication. Starlette reflects request origins for credentialed access.
- Risk: where the browser permits the cross-site cookie, an untrusted website could read private company data or perform actions as a signed-in employee. An owner session could permit creation of another owner account. Production configuration is not yet confirmed.
- Recommended remediation: exact trusted-origin allowlist, never wildcard with credentials; add CSRF defenses and evaluate SameSite=Lax/Strict. Preserve separate authenticated bridge access.
- Verification after a fix: untrusted-origin preflight/credentialed responses rejected; trusted web/desktop login, bridge authentication, mutations, logout and owner/dispatcher controls still work. Security regression tests required.

### SEC-002 — LOW: username enumeration and targeted lockout
- Evidence: login only performs bcrypt comparison for an existing username; account-level lockout can be triggered by five unauthenticated wrong guesses.
- Risk: timing-based username discovery and temporary denial of access to a known account.
- Recommended remediation: comparable dummy verification for unknown usernames and stronger client/global throttling or a safe owner recovery path, while retaining brute-force protections.

## Additional hardening
- Windows desktop bootstrap ships a known default owner password. Replace with first-run password setup/change; do not publish credential values in reports.
- Browser stores JWT in localStorage in addition to an HttpOnly cookie. Prefer one appropriately protected browser session channel, while retaining explicit bearer tokens for the local bridge.
- Protect/rotate deployment credentials and signing secrets; production strength/permissions not inspected. Plaintext environment storage alone is not evidence of exposure.

## Reviewed without a material issue identified
Parameterized database queries, owner-only destructive actions, telemetry source ownership, loopback restrictions, encrypted backup schema/FK validation, CSV escaping, obvious path traversal/XSS sinks. This is not a guarantee that all vulnerabilities are absent.

## Next steps
1. Remediate SEC-001, preserving legitimate browser/desktop/bridge workflows.
2. Run security regression tests after any changes and repeat audit of the changed controls.
3. Verify actual production origin/cookie/TLS/secret configuration separately; no production-runtime assurance can be issued from this audit.