import { useState } from "react";
import CrudPage from "@/components/CrudPage";
import { Kpi, Panel, StatusBadge } from "@/components/Bits";
import { useFetch } from "@/hooks/useData";
import { money, today } from "@/lib/api";

const RESULTS = ["Passed", "Fined", "Out of Service"];

const cfg = {
  endpoint: "inspections",
  kicker: "Safety",
  title: "DOT inspections",
  singular: "Inspection",
  description: "Fine amount and reason only apply when the result is Fined or Out of Service.",
  defaults: () => ({ date: today(), result: "Passed" }),
  fields: (form) => [
    { name: "date", label: "Date", type: "date", required: true },
    { name: "result", label: "Result", type: "select", options: RESULTS, required: true },
    { name: "driver_id", label: "Driver", type: "select", lookup: "drivers" },
    { name: "truck_id", label: "Truck", type: "select", lookup: "trucks" },
    { name: "location", label: "Location", full: true, placeholder: "e.g. Ehrenberg, AZ weigh station" },
    ...(form.__all || (form.result && form.result !== "Passed")
      ? [
          { name: "fine_amount", label: "Fine amount ($)", type: "number" },
          { name: "fine_reason", label: "Fine reason", placeholder: "e.g. Overweight, logbook" },
        ]
      : []),
    { name: "notes", label: "Notes", type: "textarea", full: true },
  ],
  columns: [
    { key: "date", label: "Date", mono: true },
    { key: "result", label: "Result", render: (r) => <StatusBadge value={r.result} testId={`inspection-result-${r.id}`} /> },
    { key: "driver_name", label: "Driver" },
    { key: "truck_number", label: "Truck", mono: true, render: (r) => (r.truck_number ? `#${r.truck_number}` : "—") },
    { key: "location", label: "Location" },
    { key: "fine_reason", label: "Fine reason" },
    { key: "fine_amount", label: "Fine", right: true, render: (r) => (r.fine_amount ? <span className="text-amber-400">{money(r.fine_amount)}</span> : "—") },
  ],
};

export default function Inspections() {
  const [s, reload] = useFetch("/stats/inspections");
  const [result, setResult] = useState("all");
  const filter = result === "all" ? null : (r) => r.result === result;
  const counts = Object.fromEntries((s?.by_result || []).map((r) => [r.result, r.count]));
  const toolbar = (
    <div className="flex flex-wrap gap-1" data-testid="inspections-result-filter">
      {["all", ...RESULTS].map((x) => (
        <button key={x} data-testid={`inspections-filter-${x.replace(/ /g, "-").toLowerCase()}`} onClick={() => setResult(x)}
          className={`rounded-md px-3 py-1.5 text-xs transition-colors ${result === x ? "bg-amber-500 text-slate-950" : "bg-slate-800 text-slate-400 hover:text-white"}`}>
          {x === "all" ? "All" : x}
        </button>
      ))}
    </div>
  );
  return (
    <CrudPage cfg={{ ...cfg, toolbar }} filter={filter} onChanged={reload}>
      <div className="mb-6 grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <div className="grid grid-cols-2 gap-4">
          <Kpi testId="insp-kpi-passed" label="Passed" value={counts.Passed || 0} tone="emerald" />
          <Kpi testId="insp-kpi-fined" label="Fined" value={counts.Fined || 0} tone="amber" />
          <Kpi testId="insp-kpi-oos" label="Out of service" value={counts["Out of Service"] || 0} tone="rose" />
          <Kpi testId="insp-kpi-fines" label="Total fines" value={money(s?.fines_total)} tone="amber" />
        </div>
        <Panel title="Fines by reason" testId="fines-by-reason">
          {!s?.by_reason?.length ? (
            <div className="py-6 text-center font-mono text-xs text-slate-600">No fines recorded</div>
          ) : (
            <div className="space-y-2">
              {s.by_reason.map((r) => {
                const max = s.by_reason[0].total || 1;
                return (
                  <div key={r.reason} data-testid={`fine-reason-${r.reason}`} className="text-sm">
                    <div className="mb-1 flex justify-between">
                      <span>{r.reason} <span className="font-mono text-xs text-slate-500">×{r.count}</span></span>
                      <span className="font-mono text-amber-400">{money(r.total)}</span>
                    </div>
                    <div className="h-1.5 rounded bg-slate-800"><div className="h-1.5 rounded bg-amber-500" style={{ width: `${(r.total / max) * 100}%` }} /></div>
                  </div>
                );
              })}
            </div>
          )}
        </Panel>
      </div>
    </CrudPage>
  );
}
