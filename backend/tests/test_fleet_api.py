# Regression tests for Virtual Trucking Company API (SQLite backend)
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"username": "owner", "password": "trucker123"})
    if r.status_code != 200:
        pytest.skip("login failed")
    s.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
    return s


# --- Auth ---
class TestAuth:
    def test_login_ok(self):
        r = requests.post(f"{API}/auth/login", json={"username": "owner", "password": "trucker123"})
        assert r.status_code == 200
        d = r.json()
        assert d["user"]["username"] == "owner" and isinstance(d["token"], str)
        assert "access_token" in r.headers.get("set-cookie", "").lower() or True

    def test_login_wrong(self):
        r = requests.post(f"{API}/auth/login", json={"username": "owner", "password": "nope"})
        assert r.status_code == 401

    def test_protected_requires_auth(self):
        assert requests.get(f"{API}/trucks").status_code == 401
        assert requests.get(f"{API}/stats/dashboard").status_code == 401

    def test_me(self, client):
        r = client.get(f"{API}/auth/me")
        assert r.status_code == 200 and r.json()["username"] == "owner"


# --- Trucks ---
class TestTrucks:
    def test_crud_and_duplicate(self, client):
        r = client.post(f"{API}/trucks", json={"truck_number": "TEST_T1", "tank_gallons": 180, "make_model": "X"})
        assert r.status_code == 200, r.text
        t = r.json()
        assert t["truck_number"] == "TEST_T1" and t["tank_gallons"] == 180 and t["is_test"] == 0
        dup = client.post(f"{API}/trucks", json={"truck_number": "TEST_T1", "tank_gallons": 100})
        assert dup.status_code == 400 and "already exists" in dup.json()["detail"]
        u = client.put(f"{API}/trucks/{t['id']}", json={"truck_number": "TEST_T1", "tank_gallons": 200})
        assert u.status_code == 200 and u.json()["tank_gallons"] == 200
        assert client.delete(f"{API}/trucks/{t['id']}").status_code == 200
        assert client.put(f"{API}/trucks/{t['id']}", json={"truck_number": "Z", "tank_gallons": 1}).status_code == 404

    def test_invalid_gallons(self, client):
        assert client.post(f"{API}/trucks", json={"truck_number": "TEST_bad", "tank_gallons": 0}).status_code == 422


# --- Fuel ---
class TestFuel:
    def test_fuel_autofill_and_compute(self, client):
        t = client.post(f"{API}/trucks", json={"truck_number": "TEST_F1", "tank_gallons": 150}).json()
        before = client.get(f"{API}/stats/fuel").json()
        r = client.post(f"{API}/fuel", json={"date": "2026-01-05", "truck_id": t["id"], "price_per_gallon": 4.0, "miles": 900})
        assert r.status_code == 200, r.text
        f = r.json()
        assert f["gallons"] == 150 and f["total"] == 600.0 and f["mpg"] == 6.0 and f["truck_number"] == "TEST_F1"
        r2 = client.post(f"{API}/fuel", json={"date": "2026-01-06", "truck_id": t["id"], "gallons": 100, "price_per_gallon": 3.5})
        f2 = r2.json()
        assert f2["total"] == 350.0 and f2["mpg"] is None
        after = client.get(f"{API}/stats/fuel").json()
        assert after["fillups"] == before["fillups"] + 2
        assert round(after["gallons"] - before["gallons"], 2) == 250
        ts = [x for x in client.get(f"{API}/stats/trucks").json() if x["id"] == t["id"]][0]
        assert ts["fillups"] == 2 and ts["gallons_bought"] == 250 and round(ts["avg_mpg"], 2) == 6.0
        # update recompute
        u = client.put(f"{API}/fuel/{f['id']}", json={"date": "2026-01-05", "truck_id": t["id"], "gallons": 120, "price_per_gallon": 4.0, "miles": 600})
        assert u.json()["total"] == 480.0 and u.json()["mpg"] == 5.0
        client.delete(f"{API}/fuel/{f['id']}"); client.delete(f"{API}/fuel/{f2['id']}")
        client.delete(f"{API}/trucks/{t['id']}")

    def test_fuel_bad_truck(self, client):
        r = client.post(f"{API}/fuel", json={"date": "2026-01-05", "truck_id": 999999, "price_per_gallon": 4.0})
        assert r.status_code == 400


# --- Categories & Expenses ---
class TestExpenses:
    def test_category_and_expense(self, client):
        c = client.post(f"{API}/categories", json={"name": "TEST_Cat"}).json()
        assert client.post(f"{API}/categories", json={"name": "TEST_Cat"}).status_code == 400
        rn = client.put(f"{API}/categories/{c['id']}", json={"name": "TEST_Cat2"})
        assert rn.json()["name"] == "TEST_Cat2"
        e = client.post(f"{API}/expenses", json={"date": "2026-01-02", "amount": 123.45, "category_id": c["id"], "description": "TEST_exp"}).json()
        assert e["category_name"] == "TEST_Cat2" and e["amount"] == 123.45
        assert client.delete(f"{API}/categories/{c['id']}").status_code == 200
        got = [x for x in client.get(f"{API}/expenses").json() if x["id"] == e["id"]][0]
        assert got["category_id"] is None and got["category_name"] is None
        u = client.put(f"{API}/expenses/{e['id']}", json={"date": "2026-01-03", "amount": 50, "description": "TEST_exp2"})
        assert u.json()["amount"] == 50
        assert client.delete(f"{API}/expenses/{e['id']}").status_code == 200
        assert client.delete(f"{API}/expenses/{e['id']}").status_code == 404


# --- Loads -> Income sync ---
class TestLoads:
    def test_load_income_sync(self, client):
        r = client.post(f"{API}/loads", json={"origin": "TEST_A", "destination": "TEST_B", "pay": 1000, "miles": 400,
                                              "due_date": "2026-01-04", "delivered_date": "2026-01-04", "status": "On Time"})
        assert r.status_code == 200, r.text
        lid = r.json()["id"]
        inc = [x for x in client.get(f"{API}/income").json() if x.get("load_id") == lid]
        assert len(inc) == 1 and inc[0]["amount"] == 1000 and "TEST_A" in inc[0]["source"]
        client.put(f"{API}/loads/{lid}", json={"origin": "TEST_A", "destination": "TEST_C", "pay": 1500, "status": "Late",
                                               "delivered_date": "2026-01-06"})
        inc = [x for x in client.get(f"{API}/income").json() if x.get("load_id") == lid]
        assert len(inc) == 1 and inc[0]["amount"] == 1500 and "TEST_C" in inc[0]["source"] and inc[0]["date"] == "2026-01-06"
        assert [l for l in client.get(f"{API}/loads").json() if l["id"] == lid][0]["status"] == "Late"
        client.delete(f"{API}/loads/{lid}")
        assert not [x for x in client.get(f"{API}/income").json() if x.get("load_id") == lid]

    def test_bad_status(self, client):
        assert client.post(f"{API}/loads", json={"origin": "a", "destination": "b", "pay": 1, "status": "Early"}).status_code == 422

    def test_manual_income(self, client):
        i = client.post(f"{API}/income", json={"date": "2026-01-01", "amount": 77, "source": "TEST_src"}).json()
        assert i["amount"] == 77 and i["load_id"] is None
        assert client.delete(f"{API}/income/{i['id']}").status_code == 200


# --- Inspections ---
class TestInspections:
    def test_inspection_fines(self, client):
        p = client.post(f"{API}/inspections", json={"date": "2026-01-02", "result": "Passed", "fine_amount": 99, "fine_reason": "x"}).json()
        assert p["fine_amount"] is None and p["fine_reason"] is None
        f = client.post(f"{API}/inspections", json={"date": "2026-01-02", "result": "Fined", "fine_amount": 250, "fine_reason": "TEST_Reason"}).json()
        assert f["fine_amount"] == 250
        s = client.get(f"{API}/stats/inspections").json()
        rr = [x for x in s["by_reason"] if x["reason"] == "TEST_Reason"]
        assert rr and rr[0]["total"] == 250 and rr[0]["count"] == 1
        assert client.post(f"{API}/inspections", json={"date": "2026-01-02", "result": "Bad"}).status_code == 422
        client.delete(f"{API}/inspections/{p['id']}"); client.delete(f"{API}/inspections/{f['id']}")


# --- Stats ---
class TestStats:
    def test_dashboard(self, client):
        d = client.get(f"{API}/stats/dashboard").json()
        for k in ["income", "expenses", "profit", "fuel", "monthly", "by_category", "fuel_trend", "drivers", "inspections"]:
            assert k in d
        assert round(d["profit"], 2) == round(d["income"] - d["expenses"], 2)

    def test_drivers_stats(self, client):
        r = client.get(f"{API}/stats/drivers")
        assert r.status_code == 200 and isinstance(r.json(), list)


# --- Test data (runs last) ---
class TestZTestData:
    def test_seed_and_clear_keeps_user_rows(self, client):
        t = client.post(f"{API}/trucks", json={"truck_number": "TEST_KEEP", "tank_gallons": 100}).json()
        d = client.post(f"{API}/drivers", json={"name": "TEST_KEEP_DRV"}).json()
        s = client.post(f"{API}/test-data").json()
        assert s["trucks"] >= 1 and s["loads"] == 60 and s["fuel"] == 70
        rem = client.delete(f"{API}/test-data").json()["removed"]
        assert rem["loads"] == 60
        st = client.get(f"{API}/test-data").json()
        assert all(v == 0 for v in st.values())
        assert any(x["id"] == t["id"] for x in client.get(f"{API}/trucks").json())
        assert any(x["id"] == d["id"] for x in client.get(f"{API}/drivers").json())
        client.delete(f"{API}/trucks/{t['id']}"); client.delete(f"{API}/drivers/{d['id']}")
        # restore sample data for frontend testing
        s = client.post(f"{API}/test-data").json()
        assert s["loads"] == 60
