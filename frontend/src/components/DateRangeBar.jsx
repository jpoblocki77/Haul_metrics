import { CalendarRange } from "lucide-react";
import { useDateRange } from "@/context/DateRangeContext";

const PRESETS = [
  ["all", "All time"],
  ["week", "This week"],
  ["month", "This month"],
  ["last-month", "Last month"],
  ["custom", "Custom"],
];

export default function DateRangeBar() {
  const r = useDateRange();
  return (
    <div data-testid="date-range-bar" className="mb-8 flex flex-wrap items-center gap-2 rounded-lg border border-slate-800 bg-[#0F1522] px-3 py-2">
      <CalendarRange className="h-4 w-4 text-amber-500" />
      <span className="mr-1 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">Period</span>
      {PRESETS.map(([k, label]) => (
        <button
          key={k}
          data-testid={`range-${k}`}
          onClick={() => r.setPreset(k)}
          className={`rounded-md px-3 py-1 text-xs transition-colors ${r.preset === k ? "bg-amber-500 text-slate-950" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}
        >
          {label}
        </button>
      ))}
      {(r.preset === "custom" || r.start || r.end) && (
        <div className="flex items-center gap-2 font-mono text-xs">
          <input data-testid="range-start" type="date" value={r.start} onChange={(e) => r.setCustom({ start: e.target.value })} className="h-8 rounded border border-slate-700 bg-[#0B0F17] px-2" />
          <span className="text-slate-500">to</span>
          <input data-testid="range-end" type="date" value={r.end} onChange={(e) => r.setCustom({ end: e.target.value })} className="h-8 rounded border border-slate-700 bg-[#0B0F17] px-2" />
        </div>
      )}
    </div>
  );
}
