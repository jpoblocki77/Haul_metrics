# Account-change regression checklist
## CORS / CSRF regression (2026-10-29)
- Allowed browser origin is exactly configured REACT_APP_BACKEND_URL; desktop uses its exact DESKTOP_APP_ORIGIN. Legacy CORS_ORIGINS wildcard is not used.
- Untrusted Origin (including null, sibling subdomains, alternate ports/schemes, attacker-controlled Host/forwarded headers) cannot read data, log in, create owners or mutate records. Untrusted preflights must not receive an allow-origin granting access.
- Browser cookie is HttpOnly, SameSite=Lax, Secure on hosted HTTPS; only the explicit loopback desktop process may omit Secure.
- Unsafe cookie-authenticated operations require X-CSRF-Token bound to that exact access token. Missing, wrong, another-session, or stale token must be rejected before mutation; correct token succeeds. Login is JSON-only and Origin-protected.
- Authenticated GET /api/auth/csrf issues the token with Cache-Control:no-store. Browser holds it in memory, never stores a bearer JWT in localStorage. Page reload obtains a fresh CSRF token; changed-session retry is safe because middleware rejects before writes.
- Python bridge/no-Origin explicit bearer auth continues to work without a CSRF token. An untrusted browser Origin is rejected even if an Authorization header is present.
- Test login/logout, multiple browser sessions, restore/reset session revocation, owner and dispatcher roles, CRUD/account changes/backup/erase and bridge authentication against the actual preview API. Use safeguarded test records; preserve originals. Always pytest -n0.

## Existing flows
Existing username/password auth uses bcrypt, PyJWT, and SQLite (not email/OAuth).
- Read memory/test_credentials.md; log in with the current owner.
- Ensure invalid login fails and five failures trigger lockout.
- Owner can edit another user's role and reset a password; dispatchers receive 403.
- Self-demotion is blocked. Missing users return 404. Invalid roles/passwords return 422.
- Password/role change revokes old JWTs; new login works and exposes the updated role.
- seed_owner is creation-only and never overwrites passwords or roles on restart.
- Backups are encrypted and owner-only; invalid passwords/files never alter company records.
- Restore replaces records atomically, requires current owner password and explicit confirmation,
  validates references, and revokes all sessions. Restored accounts retain their backup passwords.