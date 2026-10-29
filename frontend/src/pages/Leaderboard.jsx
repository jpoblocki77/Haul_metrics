import { useState } from "react";
import { Trophy, Fuel, Clock, DollarSign } from "lucide-react";
import { PageHeader, Panel } from "@/components/Bits";
import LeaderboardHistory from "@/pages/LeaderboardHistory";
import { useFetch } from "@/hooks/useData";
import { monthRange } from "@/context/DateRangeContext";
import { money, num, pct } from "@/lib/api";

const METRICS = [
  { key: "rate", label: "On-time rate", icon: Clock, fmt: pct, tone: "text-cyan-400" },
  { key: "avg_mpg", label: "Average MPG", icon: Fuel, fmt: (v) => num(v, 2), tone: "text-blue-400" },
  { key: "revenue", label: "Revenue", icon: DollarSign, fmt: money, tone: "text-emerald-400" },
];

export function rankDrivers(stats) {
  const active = (stats || []).filter((d) => d.loads > 0).map((d) => ({ ...d, rate: (d.on_time / d.loads) * 100 }));
  const ranks = {};
  METRICS.forEach(({ key }) => {
    const vals = [...new Set(active.map((d) => d[key] ?? -1))].sort((a, b) => b - a);
    active.forEach((d) => {
      ranks[d.id] = (ranks[d.id] || 0) + vals.indexOf(d[key] ?? -1) + 1;
    });
  });
  return active.map((d) => ({ ...d, score: ranks[d.id] / METRICS.length })).sort((a, b) => a.score - b.score);
}

function RankList({ metric, drivers }) {
  const sorted = [...drivers].sort((a, b) => (b[metric.key] ?? -1) - (a[metric.key] ?? -1));
  const Icon = metric.icon;
  return (
    <Panel title={metric.label} testId={`leaderboard-${metric.key}`} action={<Icon className={`h-4 w-4 ${metric.tone}`} />}>
      <ol className="space-y-2">
        {sorted.map((d, i) => (
          <li key={d.id} data-testid={`rank-${metric.key}-${i + 1}`} className={`flex items-center gap-3 rounded-md px-3 py-2 ${i === 0 ? "bg-blue-500/10" : "bg-[#0B0F17]"}`}>
            <span className={`w-6 font-mono text-sm ${i === 0 ? "text-blue-400" : "text-slate-500"}`}>{i + 1}</span>
            <span className="flex-1 truncate text-sm">{d.name}</span>
            <span className={`font-mono text-sm ${metric.tone}`}>{metric.fmt(d[metric.key])}</span>
          </li>
        ))}
      </ol>
    </Panel>
  );
}

export default function Leaderboard() {
  const [month, setMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });
  const [stats] = useFetch("/stats/drivers", monthRange(month));
  const ranked = rankDrivers(stats);
  const top = ranked[0];
  return (
    <div data-testid="leaderboard-page">
      <PageHeader kicker="Monthly standings" title="Driver leaderboard">
        <input data-testid="leaderboard-month" type="month" value={month} onChange={(e) => e.target.value && setMonth(e.target.value)}
          className="h-10 rounded-md border border-slate-700 bg-[#111827] px-3 font-mono text-sm" />
      </PageHeader>
      {stats && !ranked.length && (
        <div data-testid="leaderboard-empty" className="rounded-lg border border-slate-800 bg-[#111827] p-10 text-center text-slate-500">No loads delivered in this month.</div>
      )}
      {top && (
        <div data-testid="top-driver-card" className="animate-rise mb-6 grid min-w-0 grid-cols-[minmax(0,1fr)] items-center gap-5 rounded-lg border border-blue-500/40 bg-gradient-to-r from-blue-500/15 to-transparent p-5 sm:grid-cols-[auto_minmax(0,1fr)] xl:grid-cols-[auto_minmax(0,1fr)_auto] sm:p-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-600 text-white"><Trophy className="h-8 w-8" /></div>
          <div className="min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-500">Top driver of the month</div>
            <div className="break-words font-heading text-3xl font-black text-foreground" style={{ overflowWrap: "anywhere" }} data-testid="top-driver-name">{top.name}</div>
            <div className="mt-1 text-xs text-slate-400">Best combined rank across on-time rate, MPG and revenue</div>
          </div>
          <div className="flex min-w-0 flex-wrap gap-4 font-mono text-sm sm:col-span-2 xl:col-span-1">
            <div><div className="text-[10px] uppercase text-slate-500">On time</div><div className="text-cyan-400">{pct(top.rate)}</div></div>
            <div><div className="text-[10px] uppercase text-slate-500">MPG</div><div className="text-blue-400">{num(top.avg_mpg, 2)}</div></div>
            <div><div className="text-[10px] uppercase text-slate-500">Revenue</div><div className="text-emerald-400">{money(top.revenue)}</div></div>
          </div>
        </div>
      )}
      {ranked.length > 0 && (
        <div className="mb-6 grid gap-6 lg:grid-cols-3">
          {METRICS.map((m) => <RankList key={m.key} metric={m} drivers={ranked} />)}
        </div>
      )}
      <LeaderboardHistory onPick={setMonth} />
    </div>
  );
}
