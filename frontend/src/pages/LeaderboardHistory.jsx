import { Trophy } from "lucide-react";
import { Panel } from "@/components/Bits";
import { useFetch } from "@/hooks/useData";
import { money, num, pct } from "@/lib/api";

const label = (m) => new Date(`${m}-15`).toLocaleDateString("en-US", { month: "long", year: "numeric" });

export default function LeaderboardHistory({ onPick }) {
  const [data] = useFetch("/stats/leaderboard-history");
  if (!data?.history?.length) return null;
  return (
    <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
      <Panel title="Trophy cabinet" testId="trophy-counts" action={<Trophy className="h-4 w-4 text-red-500" />}>
        <div className="space-y-2">
          {data.trophies.map((t, i) => (
            <div key={t.driver_id} data-testid={`trophy-${t.driver_id}`} className="flex min-w-0 flex-wrap items-center gap-2 rounded-md bg-[#0B0F17] px-3 py-2">
              <span className="w-5 font-mono text-sm text-slate-500">{i + 1}</span>
              <span className="min-w-0 flex-1 break-words text-sm">{t.name}</span>
              <span className="hidden gap-0.5 sm:flex">
                {Array.from({ length: Math.min(t.trophies, 6) }).map((_, k) => <Trophy key={k} className="h-3.5 w-3.5 text-blue-400" />)}
              </span>
              <span className="w-6 text-right font-mono text-sm text-blue-400" data-testid={`trophy-count-${t.driver_id}`}>{t.trophies}</span>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Past top drivers" testId="leaderboard-history">
        <div className="min-w-0 max-w-full overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left font-mono text-[10px] uppercase tracking-widest text-slate-500">
                <th className="py-2 pr-4">Month</th><th className="py-2 pr-4">Top driver</th>
                <th className="py-2 pr-4 text-right">On time</th><th className="py-2 pr-4 text-right">MPG</th><th className="py-2 text-right">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {data.history.map((h) => (
                <tr key={h.month} data-testid={`history-${h.month}`} onClick={() => onPick(h.month)} className="cursor-pointer border-b border-slate-800/60 transition-colors hover:bg-slate-800/40">
                  <td className="whitespace-nowrap py-2 pr-4 font-mono text-slate-400">{label(h.month)}</td>
                  <td className="whitespace-nowrap py-2 pr-4"><Trophy className="mr-2 inline h-3.5 w-3.5 text-red-500" />{h.name}</td>
                  <td className="py-2 pr-4 text-right font-mono text-cyan-400">{pct(h.rate)}</td>
                  <td className="py-2 pr-4 text-right font-mono text-blue-400">{num(h.avg_mpg, 2)}</td>
                  <td className="py-2 text-right font-mono text-emerald-400">{money(h.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
