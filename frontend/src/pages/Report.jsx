import { useState } from "react";
import { Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useFetch } from "@/hooks/useData";
import { monthRange } from "@/context/DateRangeContext";
import { rankDrivers } from "@/pages/Leaderboard";
import { money, num, pct } from "@/lib/api";

const thisMonth = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};

function Stat({ label, value, tone = "text-slate-900", testId }) {
  return (
    <div className="border-l-4 border-blue-700 pl-3">
      <div className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">{label}</div>
      <div className={`font-mono text-xl font-semibold ${tone}`} data-testid={testId}>{value}</div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="mt-6 break-inside-avoid">
      <h2 className="mb-3 border-b-2 border-red-600 pb-1 font-heading text-sm font-black uppercase tracking-wider text-blue-900">{title}</h2>
      {children}
    </section>
  );
}

const Th = ({ children, right }) => <th className={`py-1.5 pr-3 text-[10px] uppercase tracking-wider text-slate-500 ${right ? "text-right" : "text-left"}`}>{children}</th>;
const Td = ({ children, right }) => <td className={`py-1.5 pr-3 ${right ? "text-right font-mono" : ""}`}>{children}</td>;

export default function Report() {
  const [month, setMonth] = useState(thisMonth);
  const range = monthRange(month);
  const [s] = useFetch("/stats/dashboard", range);
  const [trucks] = useFetch("/stats/trucks", range);
  const title = new Date(`${month}-15`).toLocaleDateString("en-US", { month: "long", year: "numeric" });
  const drivers = rankDrivers(s?.drivers);
  const ins = Object.fromEntries((s?.inspections.by_result || []).map((r) => [r.result, r.count]));

  return (
    <div data-testid="report-page">
      <div className="no-print mb-6 flex flex-wrap items-center gap-3">
        <h1 className="mr-auto font-heading text-3xl font-black text-white">Monthly report</h1>
        <input data-testid="report-month" type="month" value={month} onChange={(e) => e.target.value && setMonth(e.target.value)} className="h-10 rounded-md border border-slate-700 bg-[#111827] px-3 font-mono text-sm" />
        <Button data-testid="print-report-btn" onClick={() => window.print()} className="bg-blue-600 font-semibold text-white hover:bg-blue-500">
          <Printer className="mr-2 h-4 w-4" /> Print / Save PDF
        </Button>
      </div>
      <div data-testid="report-sheet" className="mx-auto max-w-[8.5in] rounded bg-white p-8 text-[12px] text-slate-800 shadow-2xl print:max-w-none print:p-0 print:shadow-none">
        <header className="flex items-end justify-between border-b-4 border-blue-800 pb-3">
          <div>
            <div className="font-heading text-3xl font-black tracking-tight text-blue-900">McCOY<span className="text-red-600">/</span>TRUCKING</div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.3em] text-red-600">Monthly operations report</div>
          </div>
          <div className="text-right">
            <div className="font-heading text-xl font-bold text-slate-900" data-testid="report-title">{title}</div>
            <div className="font-mono text-[10px] text-slate-500">{range.start} – {range.end}</div>
          </div>
        </header>
        {!s ? <div className="py-10 text-center text-slate-400">Loading…</div> : (
          <>
            <Section title="Profit & loss">
              <div className="grid grid-cols-4 gap-4">
                <Stat label="Income" value={money(s.income)} tone="text-blue-800" testId="report-income" />
                <Stat label="Expenses" value={money(s.expenses)} tone="text-red-700" testId="report-expenses" />
                <Stat label="Net profit" value={money(s.profit)} tone={s.profit >= 0 ? "text-blue-900" : "text-red-700"} testId="report-profit" />
                <Stat label="DOT fines" value={money(s.fines_total)} tone="text-red-700" />
              </div>
              {s.by_category.length > 0 && (
                <table className="mt-3 w-1/2"><tbody>
                  {s.by_category.map((c) => <tr key={c.name} className="border-b border-slate-100"><Td>{c.name}</Td><Td right>{money(c.value)}</Td></tr>)}
                </tbody></table>
              )}
            </Section>
            <Section title="Fuel">
              <div className="grid grid-cols-4 gap-4">
                <Stat label="Fuel spend" value={money(s.fuel.spend)} testId="report-fuel-spend" />
                <Stat label="Gallons" value={num(s.fuel.gallons, 1)} />
                <Stat label="Avg $/gal" value={s.fuel.avg_ppg ? `$${num(s.fuel.avg_ppg, 3)}` : "—"} />
                <Stat label="Fleet avg MPG" value={num(s.fuel.avg_mpg, 2)} testId="report-mpg" />
              </div>
              <table className="mt-3 w-full">
                <thead><tr className="border-b border-slate-300"><Th>Truck</Th><Th right>Fill-ups</Th><Th right>Gallons</Th><Th right>Spend</Th><Th right>Avg MPG</Th></tr></thead>
                <tbody>{(trucks || []).filter((t) => t.fillups).map((t) => (
                  <tr key={t.id} className="border-b border-slate-100"><Td>#{t.truck_number}</Td><Td right>{t.fillups}</Td><Td right>{num(t.gallons_bought, 1)}</Td><Td right>{money(t.fuel_spend)}</Td><Td right>{num(t.avg_mpg, 2)}</Td></tr>
                ))}</tbody>
              </table>
            </Section>
            <Section title="Loads & drivers">
              <div className="grid grid-cols-4 gap-4">
                <Stat label="Loads" value={s.loads_total} testId="report-loads" />
                <Stat label="On time" value={s.loads_on_time} />
                <Stat label="Late" value={s.loads_total - s.loads_on_time} tone="text-red-700" />
                <Stat label="On-time rate" value={pct(s.on_time_rate)} />
              </div>
              <table className="mt-3 w-full">
                <thead><tr className="border-b border-slate-300"><Th>Rank</Th><Th>Driver</Th><Th right>Loads</Th><Th right>On time</Th><Th right>Avg MPG</Th><Th right>Revenue</Th></tr></thead>
                <tbody>{drivers.map((d, i) => (
                  <tr key={d.id} className="border-b border-slate-100"><Td>{i === 0 ? <span className="font-bold text-red-600">★ 1</span> : i + 1}</Td><Td>{d.name}</Td><Td right>{d.loads}</Td><Td right>{pct(d.rate)}</Td><Td right>{num(d.avg_mpg, 2)}</Td><Td right>{money(d.revenue)}</Td></tr>
                ))}</tbody>
              </table>
            </Section>
            <Section title="DOT inspections">
              <div className="grid grid-cols-4 gap-4">
                <Stat label="Passed" value={ins.Passed || 0} testId="report-passed" />
                <Stat label="Fined" value={ins.Fined || 0} tone="text-red-700" />
                <Stat label="Out of service" value={ins["Out of Service"] || 0} tone="text-red-700" />
                <Stat label="Total fines" value={money(s.fines_total)} tone="text-red-700" />
              </div>
              {s.inspections.by_reason.length > 0 && (
                <table className="mt-3 w-1/2"><tbody>
                  {s.inspections.by_reason.map((r) => <tr key={r.reason} className="border-b border-slate-100"><Td>{r.reason} ×{r.count}</Td><Td right>{money(r.total)}</Td></tr>)}
                </tbody></table>
              )}
            </Section>
            <footer className="mt-6 border-t border-slate-200 pt-2 text-right font-mono text-[9px] text-slate-400">Generated {new Date().toLocaleString()}</footer>
          </>
        )}
      </div>
    </div>
  );
}
