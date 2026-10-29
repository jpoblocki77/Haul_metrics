"""Conservative candidate detection from Funbit's documented snapshots, not gameplay events."""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from db import one

LITERS_PER_GALLON = 3.785411784
KM_PER_MILE = 1.609344


def queue(conn, user_id, key, kind, payload, now):
    conn.execute("""INSERT OR IGNORE INTO telemetry_events (user_id,event_key,kind,detected_at,payload)
        VALUES (?,?,?,?,?)""", (user_id, key, kind, now, json.dumps(payload)))


def ingest(conn, user_id, sample):
    conn.execute("BEGIN IMMEDIATE")
    source = one(conn, "SELECT * FROM telemetry_sources WHERE user_id=?", (user_id,))
    if not source or not source["enabled"] or not source["driver_id"] or not source["truck_id"]:
        return {"accepted": False, "reason": "Enable telemetry and select a driver and truck first"}
    state = json.loads(source["state"])
    if state.get("session") == sample.session_id and sample.sequence <= state.get("sequence", -1):
        return {"accepted": True, "duplicate": True}
    now = datetime.now(timezone.utc).isoformat()
    raw = sample.raw.model_dump(by_alias=True)
    game, truck, job, trailer = (raw[k] for k in ("game", "truck", "job", "trailer"))
    old = state.get("previous")
    continuous = (old and state.get("session") == sample.session_id and source["last_seen"]
                  and (datetime.fromisoformat(now) - datetime.fromisoformat(source["last_seen"])).total_seconds() < 15
                  and old["game"] == game["gameName"] and old["connected"] and game["connected"])
    if old and (game["paused"] or old["paused"] or truck["odometer"] is None or old["odometer"] is None or truck["odometer"] < old["odometer"]):
        continuous = False
    if not continuous:
        state.pop("last_fill", None)
        state.pop("stop", None)
    common = {"driver_id": source["driver_id"], "truck_id": source["truck_id"], "date": now[:10], "game": game["gameName"]}
    if game["connected"] and not game["paused"]:
        if job["sourceCity"] and job["destinationCity"] and trailer["attached"]:
            signature = json.dumps([game["gameName"], job, trailer.get("name")], sort_keys=True)
            fingerprint = hashlib.sha256(signature.encode()).hexdigest()
            if state.get("job_fingerprint") != fingerprint:
                state["job_fingerprint"] = fingerprint
                state["job_occurrence"] = uuid.uuid4().hex
            key = f"job:{user_id}:{state['job_occurrence']}"
            if state.get("queued_job") != key:
                queue(conn, user_id, key, "load", {**common, "origin": job["sourceCity"],
                    "destination": job["destinationCity"], "cargo": trailer.get("name"), "pay": job["income"],
                    "miles": None, "due_date": None, "delivered_date": None, "status": None,
                    "game_deadline": job["deadlineTime"], "note": "Job detected, not confirmed delivered. Verify completion, actual pay and On Time / Late. Game deadlines are simulated time."}, now)
                state["queued_job"] = key
        elif not job["sourceCity"] and not job["destinationCity"]:
            # Empty job data denotes a new occurrence next time; mere detachment does not.
            state.pop("job_fingerprint", None)
            state.pop("job_occurrence", None)
        if continuous and not old["paused"] and truck["fuel"] is not None and old["fuel"] is not None:
            delta = truck["fuel"] - old["fuel"]
            odo, old_odo = truck["odometer"], old["odometer"]
            stationary = odo is not None and old_odo is not None and 0 <= odo - old_odo < 0.1 and abs(truck["speed"] or 0) < 1
            capacity = truck["fuelCapacity"]
            valid = stationary and capacity and 0 <= truck["fuel"] <= capacity + 1 and abs(delta) <= capacity
            if delta > 0.2 and valid:
                stop = state.setdefault("stop", {"key": f"fuel:{user_id}:{uuid.uuid4().hex}", "liters": 0, "stable": 0, "common": common, "odometer": odo})
                stop["liters"] += delta
                stop["stable"] = 0
            elif state.get("stop"):
                state["stop"]["stable"] += 1
        elif not continuous:
            state.pop("stop", None)
        stop = state.get("stop")
        if stop and stop["stable"] >= 3:
            gallons = round(stop["liters"] / LITERS_PER_GALLON, 4)
            previous_fill = state.get("last_fill")
            full = truck["fuelCapacity"] and truck["fuel"] is not None and truck["fuelCapacity"] - truck["fuel"] < 1
            miles = None
            if previous_fill and previous_fill["full"] and full and stop["odometer"] >= previous_fill["odometer"]:
                miles = round((stop["odometer"] - previous_fill["odometer"]) / KM_PER_MILE, 2)
            queue(conn, user_id, stop["key"], "fuel", {**stop["common"], "gallons": gallons,
                "price_per_gallon": None, "miles": miles, "location": None,
                "note": "Fuel increase detected. Confirm this was a purchase, not a save reload. Enter station price. MPG is only prefilled between consecutive full tanks."}, now)
            state["last_fill"] = {"full": bool(full), "odometer": stop["odometer"]}
            state.pop("stop", None)
    state.update(session=sample.session_id, sequence=sample.sequence, previous={
        "game": game["gameName"], "connected": game["connected"], "paused": game["paused"],
        "fuel": truck["fuel"], "odometer": truck["odometer"]})
    conn.execute("UPDATE telemetry_sources SET state=?, last_seen=? WHERE user_id=?", (json.dumps(state), now, user_id))
    return {"accepted": True}