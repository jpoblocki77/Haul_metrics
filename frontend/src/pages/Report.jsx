import { useState } from "react";
import { Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useFetch } from "@/hooks/useData";
import { monthRange } from "@/context/DateRangeContext";
import { rankDrivers } from "@/pages/Leaderboard";
import { money, num, pct, errMsg } from "@/lib/api";
import { ReportCharts } from "@/components/ReportCharts";
import { CompanyName } from "@/components/CompanyName";

const currentMonth = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; };
const Stat = ({ label, value, id }) => <div className="report-stat min-w-0 border-l-2 pl-2"><div className="text-[9px] uppercase">{label}</div><div data-testid={id} className="break-words font-mono text-base font-semibold sm:text-lg">{value}</div></div>;
const Section = ({ title, children }) => <section className="report-section mt-5 break-inside-avoid"><h2 className="report-section-title mb-2 border-b pb-1 font-heading text-sm font-bold uppercase">{title}</h2>{children}</section>;

export default function Report() {
  const [month, setMonth] = useState(currentMonth);
  const range = monthRange(month);
  const [s, reload, error] = useFetch("/stats/dashboard", range);
  const [charts, reloadCharts, chartError] = useFetch("/stats/report-charts", range);
  const title = new Date(`${month}-15`).toLocaleDateString("en-US", { month: "long", year: "numeric" });
  const drivers = rankDrivers(s?.drivers);
  const ins = Object.fromEntries((s?.inspections.by_result || []).map((r) => [r.result, r.count]));
  return <div data-testid="report-page">
    <div className="no-print mb-6 flex flex-wrap items-center gap-3"><h1 className="mr-auto font-heading text-3xl font-black">Monthly report</h1><input aria-label="Report month" data-testid="report-month" type="month" value={month} onChange={(e) => e.target.value && setMonth(e.target.value)} className="h-10 max-w-full rounded-md border border-border bg-card px-3 font-mono text-sm" /><Button data-testid="print-report-btn" disabled={!s || !charts || !!error || !!chartError} onClick={() => window.print()}><Printer className="mr-2 h-4 w-4" />Print / Save PDF</Button></div>
    {(error || chartError) && <p data-testid="report-error" role="alert" className="mb-5 text-destructive">{errMsg(error || chartError)} <Button data-testid="report-retry" onClick={() => { reload(); reloadCharts(); }}>Retry</Button></p>}
    <div data-testid="report-sheet" className="report-sheet mx-auto max-w-[8.5in] rounded p-4 text-xs sm:p-7">
      <header className="report-header flex flex-wrap items-end justify-between gap-3 border-b-4 pb-3"><div className="min-w-0 flex-1"><div className="font-heading text-xl font-black sm:text-2xl"><CompanyName testId="report-company-name" /></div><div className="text-[9px] uppercase">Monthly operations report</div></div><div><div data-testid="report-title" className="font-heading text-base font-bold">{title}</div><div className="text-[9px]">{range.start} – {range.end}</div></div></header>
      {!s || !charts ? <p data-testid="report-loading" className="py-10 text-center">Loading report…</p> : <>
        <Section title="Profit & loss"><div className="report-stats grid grid-cols-2 gap-3 sm:grid-cols-4"><Stat label="Income" value={money(s.income)} id="report-income" /><Stat label="Expenses" value={money(s.expenses)} id="report-expenses" /><Stat label="Net profit" value={money(s.profit)} id="report-profit" /><Stat label="DOT fines" value={money(s.fines_total)} id="report-fines" /></div></Section>
        <div className="mt-5"><ReportCharts data={charts} /></div>
        <Section title="Fuel"><div className="report-stats grid grid-cols-2 gap-3 sm:grid-cols-4"><Stat label="Fuel spend" value={money(s.fuel.spend)} id="report-fuel-spend" /><Stat label="Gallons" value={num(s.fuel.gallons, 1)} id="report-gallons" /><Stat label="Avg $/gal" value={num(s.fuel.avg_ppg, 3)} id="report-price" /><Stat label="Fleet avg MPG" value={num(s.fuel.avg_mpg, 2)} id="report-mpg" /></div></Section>
        <Section title="Loads & drivers"><div className="report-stats grid grid-cols-2 gap-3 sm:grid-cols-4"><Stat label="Loads" value={s.loads_total} id="report-loads" /><Stat label="On time" value={s.loads_on_time} id="report-on-time" /><Stat label="Late" value={s.loads_total - s.loads_on_time} id="report-late" /><Stat label="On-time rate" value={pct(s.on_time_rate)} id="report-on-time-rate" /></div>
          <div className="mt-3 text-[9px]" data-testid="report-driver-limit">Top {Math.min(5, drivers.length)} of {drivers.length} active drivers</div>
          <div className="report-driver-table mt-1" data-testid="report-drivers"><div className="report-driver-row font-semibold"><span>Driver</span><span>Loads</span><span>On time</span><span>MPG</span><span>Revenue</span></div>{drivers.slice(0, 5).map((d, i) => <div key={d.id} className="report-driver-row" data-testid={`report-driver-${d.id}`}><span className="break-words">{i === 0 ? "★ " : ""}{d.name}</span><span>{d.loads}</span><span>{pct(d.rate)}</span><span>{num(d.avg_mpg, 2)}</span><span>{money(d.revenue)}</span></div>)}</div>
        </Section>
        <Section title="DOT inspections"><div className="report-stats grid grid-cols-2 gap-3 sm:grid-cols-4"><Stat label="Passed" value={ins.Passed || 0} id="report-passed" /><Stat label="Fined" value={ins.Fined || 0} id="report-fined" /><Stat label="Out of service" value={ins["Out of Service"] || 0} id="report-oos" /><Stat label="Total fines" value={money(s.fines_total)} id="report-total-fines" /></div></Section>
        <footer className="mt-5 border-t pt-2 text-[9px]" data-testid="report-footer"><CompanyName testId="report-footer-company" /> · Company totals include all records for the month. US gallons / miles / USD.<span className="block">Generated {new Date().toLocaleString()}</span></footer>
      </>}
    </div>
  </div>;
}