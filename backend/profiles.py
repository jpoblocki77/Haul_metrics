"""Driver detail and day-by-day report series."""
from fastapi import APIRouter, Depends, HTTPException
from db import get_conn, one, rows
from auth import get_current_user


def build_router(driver_performance, leaderboard_history, list_table, period):
    router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])

    @router.get("/drivers/{driver_id}/profile")
    def profile(driver_id: int, p=Depends(period)):
        with get_conn() as conn:
            driver = one(conn, "SELECT * FROM drivers WHERE id = ?", (driver_id,))
            if not driver:
                raise HTTPException(404, "Driver not found")
            stats = next(d for d in driver_performance(conn, p) if d["id"] == driver_id)
            records = {}
            for table in ("loads", "fuel", "inspections"):
                col = "COALESCE(x.delivered_date,x.due_date)" if table == "loads" else "x.date"
                records[table] = list_table(conn, table,
                    f"WHERE x.driver_id = :driver AND (:s IS NULL OR {col} >= :s) AND (:e IS NULL OR {col} <= :e)",
                    {**p, "driver": driver_id})
            trend = rows(conn, """SELECT date, SUM(miles)/SUM(gallons) AS mpg FROM fuel
                WHERE driver_id = :driver AND miles > 0 AND (:s IS NULL OR date >= :s)
                AND (:e IS NULL OR date <= :e) GROUP BY date ORDER BY date""", {**p, "driver": driver_id})
        trophies = [h for h in leaderboard_history()["history"] if h["driver_id"] == driver_id]
        return {"driver": driver, "stats": stats, **records, "mpg_trend": trend, "trophies": trophies}

    @router.get("/stats/report-charts")
    def report_charts(p=Depends(period)):
        with get_conn() as conn:
            cash = rows(conn, """SELECT date, SUM(inc) AS income, SUM(exp) AS expenses FROM (
                SELECT date, amount AS inc, 0 AS exp FROM income
                UNION ALL SELECT date, 0, amount FROM expenses
                UNION ALL SELECT date, 0, total FROM fuel
                UNION ALL SELECT date, 0, COALESCE(fine_amount,0) FROM inspections
                ) WHERE (:s IS NULL OR date >= :s) AND (:e IS NULL OR date <= :e)
                GROUP BY date ORDER BY date""", p)
            fuel = rows(conn, """SELECT date, SUM(miles)/SUM(gallons) AS mpg FROM fuel
                WHERE miles > 0 AND (:s IS NULL OR date >= :s) AND (:e IS NULL OR date <= :e)
                GROUP BY date ORDER BY date""", p)
        return {"cash": cash, "fuel": fuel}

    return router