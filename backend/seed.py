import random
from datetime import date, timedelta

from db import get_conn, one

TRUCKS = [("101", 150, "Peterbilt 579"), ("102", 200, "Kenworth W900"), ("103", 150, "Freightliner Cascadia"),
          ("104", 125, "Volvo VNL 860"), ("105", 240, "Mack Anthem"), ("106", 150, "International LT")]
DRIVERS = ["Mike \"Gearjammer\" Lopez", "Sarah Kent", "Dale Rivers", "Tasha Brooks", "Ray Holloway", "Jenny Park"]
CITIES = ["Los Angeles, CA", "Phoenix, AZ", "Las Vegas, NV", "Denver, CO", "Dallas, TX", "Salt Lake City, UT",
          "Portland, OR", "Seattle, WA", "Albuquerque, NM", "Boise, ID", "Sacramento, CA", "El Paso, TX"]
CARGO = ["Lumber", "Frozen Food", "Electronics", "Steel Coils", "Gravel", "Furniture", "Fertilizer", "Car Parts"]
EXPENSES = [("Repairs", 300, 2500), ("Tolls", 15, 120), ("Insurance", 400, 900), ("Driver Pay", 800, 2200),
            ("Tires", 400, 1600), ("Permits", 50, 300)]
FINE_REASONS = ["Overweight", "Logbook violation", "Speeding", "Brake defect", "Lighting violation", "Missing permit"]


def seed_test_data():
    rnd = random.Random()
    today = date.today()
    with get_conn() as conn:
        truck_ids = []
        for num, gal, model in TRUCKS:
            number = f"T-{num}"
            while one(conn, "SELECT id FROM trucks WHERE truck_number = ?", (number,)):
                number += "S"
            cur = conn.execute("INSERT INTO trucks (truck_number, tank_gallons, make_model, is_test) VALUES (?,?,?,1)",
                               (number, gal, model))
            truck_ids.append(cur.lastrowid)
        trucks = {r[0]: r[1] for r in conn.execute("SELECT id, tank_gallons FROM trucks WHERE id IN (%s)" %
                                                    ",".join("?" * len(truck_ids)), truck_ids)}
        driver_ids = [conn.execute("INSERT INTO drivers (name, is_test) VALUES (?,1)", (n,)).lastrowid for n in DRIVERS]
        crew = list(zip(driver_ids, truck_ids))

        cat_ids = {}
        for name, _, _ in EXPENSES:
            c = one(conn, "SELECT id FROM categories WHERE name = ?", (name,))
            cat_ids[name] = c["id"] if c else conn.execute(
                "INSERT INTO categories (name, is_test) VALUES (?,1)", (name,)).lastrowid

        for i in range(60):
            d_id, t_id = rnd.choice(crew)
            due = today - timedelta(days=rnd.randint(0, 180))
            late = rnd.random() < 0.18
            delivered = due + timedelta(days=rnd.randint(1, 2)) if late else due - timedelta(days=rnd.randint(0, 1))
            origin, dest = rnd.sample(CITIES, 2)
            miles = rnd.randint(250, 1400)
            pay = round(miles * rnd.uniform(2.1, 3.4), 2)
            lid = conn.execute(
                "INSERT INTO loads (origin, destination, cargo, driver_id, truck_id, pay, miles, due_date, delivered_date, status, is_test) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,1)",
                (origin, dest, rnd.choice(CARGO), d_id, t_id, pay, miles, due.isoformat(), delivered.isoformat(),
                 "Late" if late else "On Time")).lastrowid
            conn.execute("INSERT INTO income (date, amount, source, driver_id, truck_id, load_id, is_test) VALUES (?,?,?,?,?,?,1)",
                         (delivered.isoformat(), pay, f"Load: {origin} → {dest}", d_id, t_id, lid))

        for i in range(8):
            d_id, t_id = rnd.choice(crew)
            conn.execute("INSERT INTO income (date, amount, source, driver_id, truck_id, notes, is_test) VALUES (?,?,?,?,?,?,1)",
                         ((today - timedelta(days=rnd.randint(0, 180))).isoformat(), round(rnd.uniform(200, 1500), 2),
                          rnd.choice(["Convoy event bonus", "Sponsorship", "Detention pay"]), d_id, t_id, ""))

        for i in range(70):
            d_id, t_id = rnd.choice(crew)
            tank = trucks[t_id]
            gallons = tank if rnd.random() < 0.6 else round(tank * rnd.uniform(0.4, 0.9), 1)
            ppg = round(rnd.uniform(3.45, 5.10), 3)
            mpg_true = rnd.uniform(5.4, 7.8)
            miles = round(gallons * mpg_true)
            conn.execute(
                "INSERT INTO fuel (date, truck_id, driver_id, gallons, price_per_gallon, total, miles, mpg, location, is_test) "
                "VALUES (?,?,?,?,?,?,?,?,?,1)",
                ((today - timedelta(days=rnd.randint(0, 180))).isoformat(), t_id, d_id, gallons, ppg,
                 round(gallons * ppg, 2), miles, round(miles / gallons, 2), rnd.choice(CITIES)))

        for i in range(40):
            name, lo, hi = rnd.choice(EXPENSES)
            d_id, t_id = rnd.choice(crew)
            conn.execute("INSERT INTO expenses (date, amount, category_id, driver_id, truck_id, description, is_test) VALUES (?,?,?,?,?,?,1)",
                         ((today - timedelta(days=rnd.randint(0, 180))).isoformat(), round(rnd.uniform(lo, hi), 2),
                          cat_ids[name], d_id, t_id, f"{name} - sample"))

        for i in range(20):
            d_id, t_id = rnd.choice(crew)
            r = rnd.random()
            result = "Passed" if r < 0.6 else ("Fined" if r < 0.88 else "Out of Service")
            fined = result != "Passed" and rnd.random() < (1 if result == "Fined" else 0.5)
            conn.execute(
                "INSERT INTO inspections (date, driver_id, truck_id, location, result, fine_amount, fine_reason, notes, is_test) "
                "VALUES (?,?,?,?,?,?,?,?,1)",
                ((today - timedelta(days=rnd.randint(0, 180))).isoformat(), d_id, t_id,
                 rnd.choice(CITIES) + " weigh station", result,
                 round(rnd.uniform(150, 1200), 2) if fined else None,
                 rnd.choice(FINE_REASONS) if fined or result == "Out of Service" else None, ""))


def clear_test_data():
    with get_conn() as conn:
        counts = {}
        for t in ["income", "expenses", "fuel", "inspections", "loads", "drivers", "trucks"]:
            counts[t] = conn.execute(f"DELETE FROM {t} WHERE is_test = 1").rowcount
        counts["categories"] = conn.execute(
            "DELETE FROM categories WHERE is_test = 1 AND id NOT IN (SELECT category_id FROM expenses WHERE category_id IS NOT NULL)"
        ).rowcount
        return counts


def test_data_status():
    with get_conn() as conn:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t} WHERE is_test = 1").fetchone()[0]
                for t in ["trucks", "drivers", "loads", "income", "expenses", "fuel", "inspections"]}
