import re
def sub(path, pairs):
    s = open(path).read()
    for a, b in pairs:
        assert a in s, (path, a)
        s = s.replace(a, b)
    open(path, "w").write(s)

B = "/app/backend/"
sub(B + "db.py", [
    ("  password_hash TEXT NOT NULL,\n", "  password_hash TEXT NOT NULL,\n  role TEXT NOT NULL DEFAULT 'dispatcher',\n"),
    ("        conn.executescript(SCHEMA)\n", "        conn.executescript(SCHEMA)\n        cols = [r[1] for r in conn.execute(\"PRAGMA table_info(users)\")]\n        if \"role\" not in cols:\n            conn.execute(\"ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'dispatcher'\")\n"),
])
sub(B + "auth.py", [
    ('user = one(conn, "SELECT id, username FROM users WHERE id = ?"', 'user = one(conn, "SELECT id, username, role FROM users WHERE id = ?"'),
    ('conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hash_password(password)))',
     'conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, \'owner\')", (username, hash_password(password)))'),
    ('        elif not verify_password(password, existing["password_hash"]):',
     '        else:\n            conn.execute("UPDATE users SET role = \'owner\' WHERE id = ?", (existing["id"],))\n        if existing and not verify_password(password, existing["password_hash"]):'),
])
s = open(B + "auth.py").read()
s += '''

def require_owner(request: Request) -> dict:
    user = get_current_user(request)
    if user["role"] != "owner":
        raise HTTPException(403, "Only an owner can do this")
    return user
'''
open(B + "auth.py", "w").write(s)
sub(B + "server.py", [
    ("from auth import hash_password, verify_password, create_token, get_current_user, seed_owner",
     "from auth import hash_password, verify_password, create_token, get_current_user, seed_owner, require_owner"),
    ('    @secure.delete(f"/{table}/{{rid}}", name=f"delete_{table}")', '    @secure.delete(f"/{table}/{{rid}}", name=f"delete_{table}", dependencies=[Depends(require_owner)])'),
    ('return {"token": token, "user": {"id": user["id"], "username": user["username"]}}', 'return {"token": token, "user": {"id": user["id"], "username": user["username"], "role": user["role"]}}'),
    ('    password: str = Field(min_length=6)\n\n\n@secure.get("/users")\ndef list_users():',
     '    password: str = Field(min_length=6)\n    role: Literal["owner", "dispatcher"] = "dispatcher"\n\n\n@secure.get("/users", dependencies=[Depends(require_owner)])\ndef list_users():'),
    ('"SELECT id, username, created_at FROM users ORDER BY id"', '"SELECT id, username, role, created_at FROM users ORDER BY id"'),
    ('@secure.post("/users")', '@secure.post("/users", dependencies=[Depends(require_owner)])'),
    ('''        uid = conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                           (username, hash_password(body.password))).lastrowid
        return one(conn, "SELECT id, username, created_at FROM users WHERE id = ?", (uid,))''',
     '''        uid = conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                           (username, hash_password(body.password), body.role)).lastrowid
        return one(conn, "SELECT id, username, role, created_at FROM users WHERE id = ?", (uid,))'''),
    ('def delete_user(uid: int, user=Depends(get_current_user)):', 'def delete_user(uid: int, user=Depends(require_owner)):'),
    ('@secure.post("/test-data")', '@secure.post("/test-data", dependencies=[Depends(require_owner)])'),
    ('@secure.delete("/test-data")', '@secure.delete("/test-data", dependencies=[Depends(require_owner)])'),
    ('# ---------- CSV export ----------', '''def rank_drivers(stats):
    active = [dict(d, rate=d["on_time"] / d["loads"] * 100) for d in stats if d["loads"]]
    score = {d["id"]: 0 for d in active}
    for key in ("rate", "avg_mpg", "revenue"):
        vals = sorted({d[key] if d[key] is not None else -1 for d in active}, reverse=True)
        for d in active:
            score[d["id"]] += vals.index(d[key] if d[key] is not None else -1) + 1
    return sorted(active, key=lambda d: score[d["id"]])


@secure.get("/stats/leaderboard-history")
def leaderboard_history():
    with get_conn() as conn:
        months = [r["m"] for r in rows(conn, """SELECT DISTINCT substr(COALESCE(delivered_date, due_date),1,7) AS m
            FROM loads WHERE COALESCE(delivered_date, due_date) IS NOT NULL AND driver_id IS NOT NULL ORDER BY m DESC""")]
        history = []
        for m in months:
            ranked = rank_drivers(driver_performance(conn, {"s": f"{m}-01", "e": f"{m}-31"}))
            if ranked:
                w = ranked[0]
                history.append({"month": m, "driver_id": w["id"], "name": w["name"], "rate": w["rate"],
                                "avg_mpg": w["avg_mpg"], "revenue": w["revenue"], "loads": w["loads"]})
    trophies = {}
    for h in history:
        t = trophies.setdefault(h["driver_id"], {"driver_id": h["driver_id"], "name": h["name"], "trophies": 0, "months": []})
        t["trophies"] += 1
        t["months"].append(h["month"])
    return {"history": history, "trophies": sorted(trophies.values(), key=lambda t: -t["trophies"])}


# ---------- CSV export ----------'''),
])
print("ok")
