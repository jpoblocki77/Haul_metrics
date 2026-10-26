import CrudPage from "@/components/CrudPage";
import { Kpi } from "@/components/Bits";
import { useRangedFetch } from "@/hooks/useData";
import { money, num, today } from "@/lib/api";

function calc(form) {
  const g = parseFloat(form.gallons);
  const p = parseFloat(form.price_per_gallon);
  const m = parseFloat(form.miles);
  return { total: g > 0 && p > 0 ? g * p : null, mpg: g > 0 && m > 0 ? m / g : null };
}

const cfg = {
  dateKey: "date",
  exportable: true,
  endpoint: "fuel",
  kicker: "Fuel log",
  title: "Fuel & MPG",
  singular: "Fuel purchase",
  description: "Pick a truck and the gallons fill in with its tank size. Change it for a partial fill.",
  defaults: () => ({ date: today() }),
  onFieldChange: (name, value, form, lookups) => {
    if (name === "truck_id") {
      const t = lookups.trucks.find((x) => String(x.id) === String(value));
      if (t) return { ...form, gallons: String(t.tank_gallons) };
    }
    return form;
  },
  fields: [
    { name: "date", label: "Date", type: "date", required: true },
    { name: "truck_id", label: "Truck number", type: "select", lookup: "trucks", required: true },
    { name: "gallons", label: "Gallons bought", type: "number", required: true, hint: "Auto-filled from truck tank size" },
    { name: "price_per_gallon", label: "Price per gallon ($)", type: "number", required: true },
    { name: "miles", label: "Miles since last fill", type: "number", hint: "Used to work out MPG" },
    { name: "driver_id", label: "Driver", type: "select", lookup: "drivers" },
    { name: "location", label: "Location / station", full: true },
  ],
  preview: (form) => {
    const { total, mpg } = calc(form);
    return (
      <div className="grid grid-cols-2 gap-3 rounded-md border border-amber-500/30 bg-amber-500/5 p-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-widest text-slate-500">Purchase total</div>
          <div className="font-mono text-2xl font-semibold text-amber-400" data-testid="fuel-total-preview">{total == null ? "—" : money(total)}</div>
        </div>
        <div>
          <div className="font-mono text-[10px] uppercase tracking-widest text-slate-500">MPG</div>
          <div className="font-mono text-2xl font-semibold text-cyan-400" data-testid="fuel-mpg-preview">{mpg == null ? "—" : num(mpg, 2)}</div>
        </div>
      </div>
    );
  },
  columns: [
    { key: "date", label: "Date", mono: true },
    { key: "truck_number", label: "Truck", mono: true, render: (r) => (r.truck_number ? `#${r.truck_number}` : "—") },
    { key: "driver_name", label: "Driver" },
    { key: "gallons", label: "Gallons", right: true, render: (r) => num(r.gallons, 1) },
    { key: "price_per_gallon", label: "$/gal", right: true, render: (r) => `$${num(r.price_per_gallon, 3)}` },
    { key: "total", label: "Total", right: true, render: (r) => <span className="text-amber-400">{money(r.total)}</span> },
    { key: "miles", label: "Miles", right: true, render: (r) => num(r.miles, 0) },
    { key: "mpg", label: "MPG", right: true, render: (r) => <span className="text-cyan-400">{num(r.mpg, 2)}</span> },
    { key: "location", label: "Location" },
  ],
};

export default function FuelPage() {
  const [s, reload] = useRangedFetch("/stats/fuel");
  return (
    <CrudPage cfg={cfg} onChanged={reload}>
      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-5">
        <Kpi testId="fuel-kpi-avg-mpg" label="Company avg MPG" value={num(s?.avg_mpg, 2)} tone="cyan" />
        <Kpi testId="fuel-kpi-gallons" label="Gallons bought" value={num(s?.gallons, 1)} />
        <Kpi testId="fuel-kpi-spend" label="Fuel spend" value={money(s?.spend)} tone="amber" />
        <Kpi testId="fuel-kpi-ppg" label="Avg price / gal" value={s?.avg_ppg ? `$${num(s.avg_ppg, 3)}` : "—"} />
        <Kpi testId="fuel-kpi-fillups" label="Fill-ups" value={s?.fillups ?? "—"} />
      </div>
    </CrudPage>
  );
}
