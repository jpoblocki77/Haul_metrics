# Account-change regression checklist
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