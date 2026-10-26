import CrudPage from "@/components/CrudPage";
import { Panel } from "@/components/Bits";
import { DriverBars } from "@/components/Charts";
import { useFetch } from "@/hooks/useData";
import { money, num, pct } from "@/lib/api";

export default function Drivers() {
  const [stats, reload] = useFetch("/stats/drivers");
  const byId = Object.fromEntries((stats || []).map((s) => [s.id, s]));
  const st = (r) => byId[r.id] || {};
  const rate = (s) => (s.loads ? (s.on_time / s.loads) * 100 : null);
  const cfg = {
    endpoint: "drivers",
    kicker: "Crew",
    title: "Drivers & performance",
    singular: "Driver",
    reloadLookups: true,
    deleteWarning: "Their past loads, fuel and inspections stay but will no longer be linked to this driver.",
    fields: [
      { name: "name", label: "Name", required: true, full: true },
      { name: "notes", label: "Notes", type: "textarea", full: true },
    ],
    columns: [
      { key: "name", label: "Driver", render: (r) => <span className="font-medium text-white">{r.name}</span> },
      { key: "loads", label: "Loads", right: true, render: (r) => st(r).loads ?? 0 },
      { key: "revenue", label: "Revenue", right: true, render: (r) => <span className="text-emerald-400">{money(st(r).revenue)}</span> },
      { key: "load_miles", label: "Miles", right: true, render: (r) => num(st(r).load_miles, 0) },
      { key: "on_time", label: "On time", right: true, render: (r) => <span className="text-cyan-400">{pct(rate(st(r)))}</span> },
      { key: "late", label: "Late", right: true, render: (r) => <span className="text-rose-400">{st(r).late ?? 0}</span> },
      { key: "avg_mpg", label: "Avg MPG", right: true, render: (r) => num(st(r).avg_mpg, 2) },
      { key: "gallons", label: "Gallons", right: true, render: (r) => num(st(r).gallons, 0) },
      { key: "insp", label: "DOT P / F / OOS", right: true, render: (r) => `${st(r).passed ?? 0} / ${st(r).fined ?? 0} / ${st(r).oos ?? 0}` },
      { key: "fines_total", label: "Fines", right: true, render: (r) => <span className="text-amber-400">{money(st(r).fines_total)}</span> },
    ],
  };
  const chart = (stats || []).filter((s) => s.loads).map((s) => ({ ...s, rate: rate(s) }));
  return (
    <CrudPage cfg={cfg} onChanged={reload}>
      {chart.length > 0 && (
        <div className="mb-6 grid gap-6 lg:grid-cols-3">
          <Panel title="Revenue by driver" testId="chart-drivers-revenue">
            <div className="h-60"><DriverBars data={chart} dataKey="revenue" name="Revenue" color="#10B981" fmt={(v) => money(v)} /></div>
          </Panel>
          <Panel title="On-time % by driver" testId="chart-drivers-ontime">
            <div className="h-60"><DriverBars data={chart} dataKey="rate" name="On time" color="#06B6D4" fmt={(v) => `${Number(v).toFixed(0)}%`} /></div>
          </Panel>
          <Panel title="Avg MPG by driver" testId="chart-drivers-mpg">
            <div className="h-60"><DriverBars data={chart.filter((c) => c.avg_mpg)} dataKey="avg_mpg" name="Avg MPG" fmt={(v) => num(v, 2)} /></div>
          </Panel>
        </div>
      )}
    </CrudPage>
  );
}
