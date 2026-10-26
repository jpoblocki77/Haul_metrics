import { useState } from "react";
import CrudPage from "@/components/CrudPage";
import { Kpi, StatusBadge } from "@/components/Bits";
import { money, num, pct, today } from "@/lib/api";

const cfg = {
  endpoint: "loads",
  kicker: "Dispatch",
  title: "Loads",
  singular: "Load",
  description: "Load pay is added to Income automatically.",
  defaults: () => ({ status: "On Time", due_date: today(), delivered_date: today() }),
  fields: [
    { name: "origin", label: "Origin", required: true, placeholder: "City, ST" },
    { name: "destination", label: "Destination", required: true, placeholder: "City, ST" },
    { name: "cargo", label: "Cargo" },
    { name: "pay", label: "Pay ($)", type: "number", required: true },
    { name: "driver_id", label: "Driver", type: "select", lookup: "drivers" },
    { name: "truck_id", label: "Truck", type: "select", lookup: "trucks" },
    { name: "miles", label: "Miles", type: "number" },
    { name: "status", label: "Delivery", type: "select", options: ["On Time", "Late"], required: true },
    { name: "due_date", label: "Due date", type: "date" },
    { name: "delivered_date", label: "Delivered date", type: "date" },
  ],
  columns: [
    { key: "delivered_date", label: "Delivered", mono: true, render: (r) => r.delivered_date || r.due_date || "—" },
    { key: "route", label: "Route", render: (r) => <>{r.origin} <span className="text-amber-500">→</span> {r.destination}</> },
    { key: "cargo", label: "Cargo" },
    { key: "driver_name", label: "Driver" },
    { key: "truck_number", label: "Truck", mono: true, render: (r) => (r.truck_number ? `#${r.truck_number}` : "—") },
    { key: "miles", label: "Miles", right: true, render: (r) => num(r.miles, 0) },
    { key: "pay", label: "Pay", right: true, render: (r) => <span className="text-emerald-400">{money(r.pay)}</span> },
    { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} testId={`load-status-${r.id}`} /> },
  ],
};

export default function Loads() {
  const [status, setStatus] = useState("all");
  const filter = status === "all" ? null : (r) => r.status === status;
  const toolbar = (
    <div className="flex gap-1" data-testid="loads-status-filter">
      {["all", "On Time", "Late"].map((s) => (
        <button key={s} data-testid={`loads-filter-${s.replace(" ", "-").toLowerCase()}`} onClick={() => setStatus(s)}
          className={`rounded-md px-3 py-1.5 text-xs transition-colors ${status === s ? "bg-amber-500 text-slate-950" : "bg-slate-800 text-slate-400 hover:text-white"}`}>
          {s === "all" ? "All" : s}
        </button>
      ))}
    </div>
  );
  return (
    <CrudPage cfg={{ ...cfg, toolbar }} filter={filter}>
      {(items) => {
        const on = items.filter((l) => l.status === "On Time").length;
        return (
          <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            <Kpi testId="loads-kpi-total" label="Loads" value={items.length} />
            <Kpi testId="loads-kpi-on-time" label="On time" value={on} tone="emerald" />
            <Kpi testId="loads-kpi-late" label="Late" value={items.length - on} tone="rose" />
            <Kpi testId="loads-kpi-rate" label="On-time rate" value={items.length ? pct((on / items.length) * 100) : "—"} tone="cyan" />
          </div>
        );
      }}
    </CrudPage>
  );
}
