# Iteration 2: users, date-range stats, CSV export, leaderboard data
import csv
import io
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


def login(u, p):
    return requests.post(f"{API}/auth/login", json={"username": u, "password": p})


@pytest.fixture(scope="module")
def client():
    r = login("owner", "trucker123")
    assert r.status_code == 200
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {r.json()['token']}"
    s.me = r.json()["user"]
    return s


# ---------- Users ----------
class TestUsers:
    def test_dispatch1_login(self):
        r = login("dispatch1", "haul1234")
        assert r.status_code == 200
        assert r.json()["user"]["username"] == "dispatch1"

    def test_list_users(self, client):
        r = client.get(f"{API}/users")
        assert r.status_code == 200
        names = [u["username"] for u in r.json()]
        assert "owner" in names and "dispatch1" in names
        assert all("password_hash" not in u for u in r.json())

    def test_create_login_delete(self, client):
        r = client.post(f"{API}/users", json={"username": "TEST_iter2", "password": "secret12"})
        assert r.status_code == 200, r.text
        u = r.json()
        assert u["username"] == "test_iter2"
        try:
            dup = client.post(f"{API}/users", json={"username": "test_iter2", "password": "secret12"})
            assert dup.status_code == 400
            assert "taken" in dup.json()["detail"]
            lr = login("TEST_iter2", "secret12")
            assert lr.status_code == 200
            assert login("test_iter2", "wrongpw").status_code == 401
        finally:
            d = client.delete(f"{API}/users/{u['id']}")
            assert d.status_code == 200
        assert "test_iter2" not in [x["username"] for x in client.get(f"{API}/users").json()]
        assert login("test_iter2", "secret12").status_code == 401
        assert client.delete(f"{API}/users/{u['id']}").status_code == 404

    def test_deleted_user_token_invalid(self, client):
        u = client.post(f"{API}/users", json={"username": "test_tok", "password": "secret12"}).json()
        tok = login("test_tok", "secret12").json()["token"]
        client.delete(f"{API}/users/{u['id']}")
        r = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401

    def test_cannot_delete_self(self, client):
        r = client.delete(f"{API}/users/{client.me['id']}")
        assert r.status_code == 400
        assert "own account" in r.json()["detail"]

    @pytest.mark.parametrize("payload", [
        {"username": "ab", "password": "secret12"},
        {"username": "bad name!", "password": "secret12"},
        {"username": "test_short", "password": "123"},
    ])
    def test_validation(self, client, payload):
        assert client.post(f"{API}/users", json=payload).status_code == 422

    def test_users_requires_auth(self):
        assert requests.get(f"{API}/users").status_code == 401


# ---------- Date range stats ----------
class TestRangeStats:
    def test_dashboard_range_changes(self, client):
        all_ = client.get(f"{API}/stats/dashboard").json()
        part = client.get(f"{API}/stats/dashboard", params={"start": "2026-09-01", "end": "2026-09-30"}).json()
        empty = client.get(f"{API}/stats/dashboard", params={"start": "1990-01-01", "end": "1990-01-31"}).json()
        assert all_["income"] > 0
        assert part["income"] <= all_["income"]
        assert empty["income"] == 0 and empty["expenses"] == 0 and empty["loads_total"] == 0
        assert empty["on_time_rate"] is None
        assert all(m["m"] == "2026-09" for m in part["monthly"])

    def test_dashboard_income_matches_list(self, client):
        s, e = "2026-09-01", "2026-09-30"
        inc = client.get(f"{API}/income").json()
        expected = sum(i["amount"] for i in inc if s <= i["date"] <= e)
        got = client.get(f"{API}/stats/dashboard", params={"start": s, "end": e}).json()["income"]
        assert abs(expected - got) < 0.01

    @pytest.mark.parametrize("ep", ["drivers", "trucks", "fuel", "inspections"])
    def test_stats_accept_range(self, client, ep):
        r = client.get(f"{API}/stats/{ep}", params={"start": "2026-09-01", "end": "2026-09-30"})
        assert r.status_code == 200
        r2 = client.get(f"{API}/stats/{ep}", params={"start": "", "end": ""})
        assert r2.status_code == 200

    def test_only_start(self, client):
        r = client.get(f"{API}/stats/fuel", params={"start": "2099-01-01"})
        assert r.status_code == 200 and r.json()["fillups"] == 0


# ---------- CSV export ----------
class TestExport:
    @pytest.mark.parametrize("table,first", [("income", "date"), ("expenses", "date"), ("fuel", "date"),
                                             ("loads", "due_date"), ("inspections", "date")])
    def test_export(self, client, table, first):
        r = client.get(f"{API}/export/{table}")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")
        assert "attachment" in r.headers.get("content-disposition", "")
        rows = list(csv.reader(io.StringIO(r.text)))
        assert rows[0][0] == first
        assert len(rows) > 1

    def test_export_range(self, client):
        s, e = "2026-09-01", "2026-09-30"
        r = client.get(f"{API}/export/income", params={"start": s, "end": e})
        data = list(csv.DictReader(io.StringIO(r.text)))
        assert all(s <= d["date"] <= e for d in data)
        expected = [i for i in client.get(f"{API}/income").json() if s <= i["date"] <= e]
        assert len(data) == len(expected)

    def test_export_unknown(self, client):
        assert client.get(f"{API}/export/users").status_code == 404

    def test_export_requires_auth(self):
        assert requests.get(f"{API}/export/income").status_code == 401
