import { Link } from "react-router-dom";
import { Kpi, PageHeader, Panel } from "@/components/Bits";
import { IncomeExpenseChart, CategoryPie, FuelTrendChart, DriverBars, SimplePie, short } from "@/components/Charts";
import { useRangedFetch } from "@/hooks/useData";
import { money, num, pct } from "@/lib/api";

export const RESULT_COLORS = { Passed: "#10B981", Fined: "#F59E0B", "Out of Service": "#F43F5E" };

export default function Dashboard() {
  const [s] = useRangedFetch("/stats/dashboard");
  if (!s) return <div className="font-mono text-sm text-slate-500">Loading dashboard…</div>;
  const drivers = s.drivers
    .filter((d) => d.loads > 0)
    .map((d) => ({ ...d, on_time_pct: (d.on_time / d.loads) * 100 }));
  const ins = Object.fromEntries(s.inspections.by_result.map((r) => [r.result, r.count]));
  const empty = s.loads_total === 0 && s.income === 0 && s.expenses === 0;

  return (
    <div data-testid="dashboard-page">
      <PageHeader kicker="Company overview" title="Dashboard" />
      {empty && (
        <div data-testid="dashboard-empty-hint" className="mb-6 rounded-lg border border-cyan-500/30 bg-cyan-500/5 p-4 text-sm text-cyan-300">
          No records yet. Start by adding trucks and drivers, or <Link to="/test-data" className="underline">load sample data</Link> to explore.
        </div>
      )}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-4">
        <Kpi testId="kpi-income" label="Total income" value={money(s.income)} tone="emerald" />
        <Kpi testId="kpi-expenses" label="Total expenses" value={money(s.expenses)} sub="Incl. fuel & DOT fines" tone="rose" delay={50} />
        <Kpi testId="kpi-profit" label="Net profit" value={money(s.profit)} tone={s.profit >= 0 ? "amber" : "rose"} delay={100} />
        <Kpi testId="kpi-on-time" label="On-time rate" value={pct(s.on_time_rate)} sub={`${s.loads_on_time} of ${s.loads_total} loads`} tone="cyan" delay={150} />
        <Kpi testId="kpi-avg-mpg" label="Fleet avg MPG" value={num(s.fuel.avg_mpg, 2)} tone="cyan" delay={200} />
        <Kpi testId="kpi-gallons" label="Gallons bought" value={num(s.fuel.gallons, 1)} sub={`Avg ${money(s.fuel.avg_ppg)}/gal`} delay={250} />
        <Kpi testId="kpi-fuel-spend" label="Fuel spend" value={money(s.fuel.spend)} tone="amber" delay={300} />
        <Kpi testId="kpi-inspections" label="DOT inspections" value={`${ins.Passed || 0} / ${ins.Fined || 0} / ${ins["Out of Service"] || 0}`} sub={`Passed / Fined / OOS · ${money(s.fines_total)} fines`} delay={350} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Panel title="Income vs expenses by month" className="xl:col-span-2" testId="chart-income-expenses">
          <div className="h-72"><IncomeExpenseChart data={s.monthly} /></div>
        </Panel>
        <Panel title="Expenses by category" testId="chart-expense-categories">
          <div className="h-72"><CategoryPie data={s.by_category} /></div>
        </Panel>
        <Panel title="Fuel cost & average MPG" className="xl:col-span-2" testId="chart-fuel-trend">
          <div className="h-72"><FuelTrendChart data={s.fuel_trend} /></div>
        </Panel>
        <Panel title="DOT inspection results" testId="chart-inspections">
          <div className="h-72"><SimplePie data={s.inspections.by_result} nameKey="result" dataKey="count" colors={RESULT_COLORS} /></div>
        </Panel>
        <Panel title="Driver revenue" testId="chart-driver-revenue">
          <div className="h-72"><DriverBars data={drivers} dataKey="revenue" name="Revenue" color="#10B981" fmt={(v) => money(v)} tickFmt={short} /></div>
        </Panel>
        <Panel title="Driver on-time %" testId="chart-driver-ontime">
          <div className="h-72"><DriverBars data={drivers} dataKey="on_time_pct" name="On time" color="#06B6D4" fmt={(v) => `${Number(v).toFixed(0)}%`} /></div>
        </Panel>
        <Panel title="Driver avg MPG" testId="chart-driver-mpg">
          <div className="h-72"><DriverBars data={s.drivers.filter((d) => d.avg_mpg)} dataKey="avg_mpg" name="Avg MPG" fmt={(v) => num(v, 2)} /></div>
        </Panel>
      </div>
    </div>
  );
}
