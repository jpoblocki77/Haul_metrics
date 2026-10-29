import { CalendarRange } from "lucide-react";
import { useDateRange } from "@/context/DateRangeContext";

const PRESETS = [
  ["all", "All time"],
  ["today", "Today"],
  ["week", "This week"],
  ["month", "This month"],
  ["last-month", "Last month"],
  ["custom", "Custom"],
];

export default function DateRangeBar() {
  const r = useDateRange();
  return (
    <div data-testid="date-range-bar" className="mb-8 flex flex-wrap items-center gap-2 rounded-lg border border-border bg-card px-3 py-2">
      <CalendarRange className="h-4 w-4 text-blue-500" />
      <span className="mr-1 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Period</span>
      {PRESETS.map(([k, label]) => (
        <button
          key={k}
          data-testid={`range-${k}`}
          onClick={() => r.setPreset(k)}
          className={`rounded-md px-3 py-1 text-xs transition-colors ${r.preset === k ? "bg-blue-600 text-white" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}
        >
          {label}
        </button>
      ))}
      {(r.preset === "custom" || r.start || r.end) && (
        <div className="flex min-w-0 flex-wrap items-center gap-2 font-mono text-xs">
          <input aria-label="Start date" data-testid="range-start" type="date" value={r.start} onChange={(e) => r.setCustom({ start: e.target.value })} className="h-8 min-w-0 max-w-full rounded border border-border bg-background px-2" />
          <span className="text-slate-500">to</span>
          <input aria-label="End date" data-testid="range-end" type="date" value={r.end} onChange={(e) => r.setCustom({ end: e.target.value })} className="h-8 min-w-0 max-w-full rounded border border-border bg-background px-2" />
        </div>
      )}
    </div>
  );
}
