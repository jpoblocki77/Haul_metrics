import CrudPage from "@/components/CrudPage";
import { Panel } from "@/components/Bits";
import { DriverBars } from "@/components/Charts";
import { useRangedFetch } from "@/hooks/useData";
import { money, num } from "@/lib/api";

export default function Trucks() {
  const [stats, reload] = useRangedFetch("/stats/trucks");
  const byId = Object.fromEntries((stats || []).map((s) => [s.id, s]));
  const st = (r, k) => byId[r.id]?.[k];
  const cfg = {
    endpoint: "trucks",
    kicker: "Fleet",
    title: "Trucks",
    singular: "Truck",
    reloadLookups: true,
    description: "The tank size is used to fill in gallons when you log fuel for this truck.",
    deleteWarning: "Past fuel, loads and expenses stay, but will no longer be linked to this truck.",
    fields: [
      { name: "truck_number", label: "Truck number", required: true, placeholder: "e.g. 101" },
      { name: "tank_gallons", label: "Tank size (gallons)", type: "number", required: true },
      { name: "make_model", label: "Make / model", full: true, placeholder: "e.g. Peterbilt 579" },
    ],
    columns: [
      { key: "truck_number", label: "Truck #", mono: true, render: (r) => <span className="text-amber-400">#{r.truck_number}</span> },
      { key: "make_model", label: "Make / model" },
      { key: "tank_gallons", label: "Tank (gal)", right: true, render: (r) => num(r.tank_gallons, 0) },
      { key: "fillups", label: "Fill-ups", right: true, render: (r) => st(r, "fillups") ?? 0 },
      { key: "gallons_bought", label: "Gallons bought", right: true, render: (r) => num(st(r, "gallons_bought"), 1) },
      { key: "fuel_spend", label: "Fuel spend", right: true, render: (r) => money(st(r, "fuel_spend")) },
      { key: "avg_mpg", label: "Avg MPG", right: true, render: (r) => <span className="text-cyan-400">{num(st(r, "avg_mpg"), 2)}</span> },
    ],
  };
  const chart = (stats || []).filter((s) => s.avg_mpg).map((s) => ({ name: `#${s.truck_number}`, avg_mpg: s.avg_mpg }));
  return (
    <CrudPage cfg={cfg} onChanged={reload}>
      {chart.length > 0 && (
        <Panel title="Average MPG by truck" className="mb-6" testId="chart-truck-mpg">
          <div className="h-56"><DriverBars data={chart} dataKey="avg_mpg" name="Avg MPG" color="#06B6D4" fmt={(v) => num(v, 2)} /></div>
        </Panel>
      )}
    </CrudPage>
  );
}
