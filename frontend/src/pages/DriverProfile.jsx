import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Trophy } from "lucide-react";
import { PageHeader, Kpi, StatusBadge } from "@/components/Bits";
import { SimpleLine } from "@/components/Charts";
import { useRangedFetch } from "@/hooks/useData";
import { money, num, pct, errMsg } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { DeleteEntryButton } from "@/components/DeleteEntryButton";

export default function DriverProfile() {
  const { id } = useParams();
  const [data, reload, error] = useRangedFetch(`/drivers/${id}/profile`);
  const [tab, setTab] = useState("loads");
  if (error) return <div data-testid="driver-profile-error" role="alert">{errMsg(error)} <Button data-testid="driver-profile-retry" onClick={reload}>Retry</Button><Link data-testid="driver-profile-error-back" to="/drivers" className="ml-3 text-primary">Drivers</Link></div>;
  if (!data) return <p data-testid="driver-profile-loading">Loading driver…</p>;
  const { driver, stats, trophies, mpg_trend } = data;
  return <div data-testid="driver-profile-page" className="min-w-0">
    <Link data-testid="driver-profile-back" to="/drivers" className="mb-5 inline-flex items-center gap-2 text-sm text-primary"><ArrowLeft size={16} /> All drivers</Link>
    <PageHeader kicker="Driver profile" title={driver.name} />
    {driver.notes && <p data-testid="driver-profile-notes" className="mb-6 break-words text-muted-foreground">{driver.notes}</p>}
    <div className="mb-8 grid grid-cols-2 gap-3 xl:grid-cols-4">
      <Kpi label="Loads" value={stats.loads} testId="profile-loads-total" />
      <Kpi label="On-time rate" value={pct(stats.loads ? stats.on_time / stats.loads * 100 : null)} testId="profile-on-time" />
      <Kpi label="Average MPG" value={num(stats.avg_mpg, 2)} testId="profile-mpg" />
      <Kpi label="Revenue" value={money(stats.revenue)} testId="profile-revenue" />
    </div>
    <div className="mb-8 grid min-w-0 gap-8 lg:grid-cols-[2fr_1fr]">
      <section className="min-w-0 border-y border-border py-5" data-testid="profile-mpg-chart"><h2 className="mb-4 font-heading text-lg font-bold">MPG trend</h2><div className="h-56"><SimpleLine data={mpg_trend} x="date" y="mpg" name="MPG" fmt={(v) => num(v, 1)} /></div></section>
      <section className="min-w-0 border-y border-border py-5" data-testid="profile-trophies"><div className="mb-4 flex items-center gap-3"><Trophy className="text-primary" /><h2 className="font-heading text-lg font-bold">Trophy cabinet</h2><span data-testid="profile-trophy-count" className="ml-auto font-mono text-xl">{trophies.length}</span></div>
        <p className="mb-4 text-xs text-muted-foreground">Top Driver · all months</p>
        {!trophies.length && <p data-testid="profile-trophies-empty" className="text-sm text-muted-foreground">No Top Driver titles yet.</p>}
        <div className="max-h-44 space-y-2 overflow-y-auto">{trophies.map((t) => <div key={t.month} data-testid={`profile-trophy-${t.month}`} className="flex justify-between border-b border-border py-2 text-sm"><span>{new Date(`${t.month}-15`).toLocaleDateString("en-US", { month: "long", year: "numeric" })}</span><Trophy size={16} className="text-primary" /></div>)}</div>
      </section>
    </div>
    <div role="tablist" aria-label="Driver records" className="mb-5 flex flex-wrap gap-2">{["loads", "fuel", "inspections"].map((key) => <Button key={key} role="tab" aria-selected={tab === key} data-testid={`profile-tab-${key}`} variant={tab === key ? "default" : "outline"} onClick={() => setTab(key)}>{key[0].toUpperCase() + key.slice(1)} ({data[key].length})</Button>)}</div>
    <section role="tabpanel" data-testid={`profile-${tab}-records`}>
      {!data[tab].length && <p data-testid="profile-records-empty" className="py-10 text-center text-muted-foreground">No {tab} in this date range.</p>}
      {data[tab].map((r) => <article key={r.id} data-testid={`profile-${tab}-${r.id}`} className="grid min-w-0 gap-3 border-b border-border py-4 sm:grid-cols-[1fr_2fr_1fr]">
        <div className="text-sm text-muted-foreground">{r.delivered_date || r.due_date || r.date || "Undated"}<div>Truck #{r.truck_number || "—"}</div></div>
        <div className="min-w-0 break-words">{tab === "loads" ? <><div className="font-medium">{r.origin} → {r.destination}</div><div className="text-sm text-muted-foreground">{r.cargo || "—"} · {num(r.miles, 0)} mi</div></> : tab === "fuel" ? <><div>{num(r.gallons, 2)} gal · {num(r.mpg, 2)} MPG</div><div className="text-sm text-muted-foreground">{r.location || "Location not recorded"}</div></> : <><div>{r.location || "Location not recorded"}</div><div className="text-sm text-muted-foreground">{r.fine_reason || r.notes || "—"}</div></>}</div>
        <div className="space-y-1 sm:text-right">{tab !== "fuel" && <StatusBadge value={r.status || r.result} testId={`profile-record-status-${tab}-${r.id}`} />}<div className="font-mono text-sm">{money(tab === "loads" ? r.pay : tab === "fuel" ? r.total : r.fine_amount || 0)}</div><DeleteEntryButton table={tab} row={r} label={tab === "loads" ? `${r.origin} → ${r.destination}` : `${tab === "fuel" ? "Fuel purchase" : r.result} · ${r.date}`} testId={`profile-delete-${tab}-${r.id}`} /></div>
      </article>)}
    </section>
  </div>;
}