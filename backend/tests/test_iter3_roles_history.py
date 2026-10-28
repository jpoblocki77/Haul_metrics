# Iteration 3: roles (owner/dispatcher), leaderboard history + trophies, monthly report stats
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


def login(u, p):
    r = requests.post(f"{API}/auth/login", json={"username": u, "password": p})
    return r


@pytest.fixture(scope="module")
def owner():
    r = login("owner", "trucker123")
    assert r.status_code == 200
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {r.json()['token']}"
    return s


@pytest.fixture(scope="module")
def disp(owner):
    r = login("dispatch1", "haul1234")
    if r.status_code != 200:
        # create dispatcher if missing
        c = owner.post(f"{API}/users", json={"username": "dispatch1", "password": "haul1234", "role": "dispatcher"})
        assert c.status_code == 200, c.text
        r = login("dispatch1", "haul1234")
    assert r.status_code == 200
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {r.json()['token']}"
    return s


# --- Auth returns role
def test_login_and_me_role(owner, disp):
    r = login("owner", "trucker123").json()
    assert r["user"]["role"] == "owner"
    assert login("dispatch1", "haul1234").json()["user"]["role"] == "dispatcher"
    assert owner.get(f"{API}/auth/me").json()["role"] == "owner"
    assert disp.get(f"{API}/auth/me").json()["role"] == "dispatcher"


# --- Dispatcher permissions
def test_dispatcher_forbidden_users(disp):
    assert disp.get(f"{API}/users").status_code == 403
    assert disp.post(f"{API}/users", json={"username": "TEST_x1", "password": "abcdef"}).status_code == 403
    assert disp.delete(f"{API}/users/1").status_code == 403


def test_dispatcher_forbidden_test_data(disp):
    assert disp.post(f"{API}/test-data").status_code == 403
    assert disp.delete(f"{API}/test-data").status_code == 403
    assert disp.get(f"{API}/test-data").status_code == 200


@pytest.mark.parametrize("table,payload", [
    ("categories", {"name": "TEST_cat_disp"}),
    ("drivers", {"name": "TEST_driver_disp"}),
    ("expenses", {"date": "2026-05-05", "amount": 12.5, "description": "TEST_exp"}),
    ("income", {"date": "2026-05-05", "amount": 99, "source": "TEST_inc"}),
])
def test_dispatcher_create_edit_but_not_delete(disp, owner, table, payload):
    c = disp.post(f"{API}/{table}", json=payload)
    assert c.status_code == 200, c.text
    rid = c.json()["id"]
    upd = dict(payload)
    key = "name" if "name" in payload else ("source" if "source" in payload else "description")
    upd[key] = payload[key] + "_edit"
    u = disp.put(f"{API}/{table}/{rid}", json=upd)
    assert u.status_code == 200 and u.json()[key] == upd[key]
    d = disp.delete(f"{API}/{table}/{rid}")
    assert d.status_code == 403
    # owner can delete
    assert owner.delete(f"{API}/{table}/{rid}").status_code == 200
    assert owner.delete(f"{API}/{table}/{rid}").status_code == 404


def test_dispatcher_delete_existing_tables_403(disp, owner):
    for t in ["trucks", "loads", "fuel", "inspections"]:
        items = owner.get(f"{API}/{t}").json()
        if items:
            assert disp.delete(f"{API}/{t}/{items[0]['id']}").status_code == 403, t


# --- Owner user management
def test_owner_create_roles_and_delete(owner):
    ids = []
    for role in ["dispatcher", "owner"]:
        r = owner.post(f"{API}/users", json={"username": f"test_{role}_u", "password": "abcdef", "role": role})
        assert r.status_code == 200, r.text
        assert r.json()["role"] == role
        ids.append(r.json()["id"])
    listed = {u["username"]: u["role"] for u in owner.get(f"{API}/users").json()}
    assert listed["test_dispatcher_u"] == "dispatcher" and listed["test_owner_u"] == "owner"
    # default role
    r = owner.post(f"{API}/users", json={"username": "test_default_u", "password": "abcdef"})
    assert r.json()["role"] == "dispatcher"
    ids.append(r.json()["id"])
    # invalid role
    assert owner.post(f"{API}/users", json={"username": "test_bad_u", "password": "abcdef", "role": "admin"}).status_code == 422
    # second owner cannot delete primary owner
    tok = login("test_owner_u", "abcdef").json()["token"]
    main_owner_id = login("owner", "trucker123").json()["user"]["id"]
    r = requests.delete(f"{API}/users/{main_owner_id}", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 400
    for i in ids:
        assert owner.delete(f"{API}/users/{i}").status_code == 200
    names = [u["username"] for u in owner.get(f"{API}/users").json()]
    assert not any(n.startswith("test_") for n in names)


def test_owner_cannot_delete_self(owner):
    me = owner.get(f"{API}/auth/me").json()
    assert owner.delete(f"{API}/users/{me['id']}").status_code == 400


# --- Leaderboard history
def test_leaderboard_history(owner):
    r = owner.get(f"{API}/stats/leaderboard-history")
    assert r.status_code == 200
    d = r.json()
    assert len(d["history"]) > 0
    assert sum(t["trophies"] for t in d["trophies"]) == len(d["history"])
    months = [h["month"] for h in d["history"]]
    assert months == sorted(months, reverse=True)
    for t in d["trophies"]:
        assert len(t["months"]) == t["trophies"]
    counts = [t["trophies"] for t in d["trophies"]]
    assert counts == sorted(counts, reverse=True)


def test_leaderboard_history_dispatcher_access(disp):
    assert disp.get(f"{API}/stats/leaderboard-history").status_code == 200


def test_history_winner_matches_monthly_rank(owner):
    """Winner per month equals the top of rankDrivers over /stats/drivers for that month."""
    d = owner.get(f"{API}/stats/leaderboard-history").json()
    import calendar
    for h in d["history"]:
        y, m = map(int, h["month"].split("-"))
        end = f"{h['month']}-{calendar.monthrange(y, m)[1]:02d}"
        stats = owner.get(f"{API}/stats/drivers", params={"start": f"{h['month']}-01", "end": end}).json()
        active = [dict(x, rate=x["on_time"] / x["loads"] * 100) for x in stats if x["loads"]]
        score = {x["id"]: 0 for x in active}
        for k in ("rate", "avg_mpg", "revenue"):
            vals = sorted({x[k] if x[k] is not None else -1 for x in active}, reverse=True)
            for x in active:
                score[x["id"]] += vals.index(x[k] if x[k] is not None else -1) + 1
        top = sorted(active, key=lambda x: score[x["id"]])[0]
        assert top["id"] == h["driver_id"], h["month"]
