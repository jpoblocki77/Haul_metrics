export function PageHeader({ kicker, title, children }) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between animate-rise">
      <div>
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-red-500">{kicker}</div>
        <h1 className="font-heading text-3xl font-black tracking-tight text-white sm:text-4xl">{title}</h1>
      </div>
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  );
}

const TONES = {
  amber: "text-blue-400", cyan: "text-cyan-400", emerald: "text-emerald-400", rose: "text-rose-400", slate: "text-slate-100",
};

export function Kpi({ label, value, sub, tone = "slate", testId, delay = 0 }) {
  return (
    <div
      data-testid={testId}
      style={{ animationDelay: `${delay}ms` }}
      className="animate-rise rounded-lg border border-slate-800 bg-[#111827] p-5 transition-colors duration-200 hover:border-slate-600"
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">{label}</div>
      <div className={`mt-2 font-mono text-2xl font-semibold tabular-nums ${TONES[tone]}`} data-testid={testId && `${testId}-value`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

export function Panel({ title, children, className = "", testId, action }) {
  return (
    <section data-testid={testId} className={`animate-rise rounded-lg border border-slate-800 bg-[#111827] p-5 ${className}`}>
      {title && (
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-heading text-sm font-bold uppercase tracking-wider text-slate-300">{title}</h3>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

const BADGE = {
  "On Time": "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  Late: "bg-rose-500/10 text-rose-400 border-rose-500/30",
  Passed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  Fined: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  "Out of Service": "bg-rose-500/10 text-rose-400 border-rose-500/30",
  Test: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
};

export function StatusBadge({ value, testId }) {
  return (
    <span data-testid={testId} className={`inline-flex items-center whitespace-nowrap rounded border px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide ${BADGE[value] || "border-slate-700 text-slate-400"}`}>
      {value}
    </span>
  );
}

export const TestTag = ({ row }) => (row?.is_test ? <span className="ml-2 rounded bg-cyan-500/10 px-1.5 font-mono text-[9px] uppercase text-cyan-400">test</span> : null);
