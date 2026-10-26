import CrudPage from "@/components/CrudPage";
import { money, today } from "@/lib/api";

const cfg = {
  dateKey: "date",
  exportable: true,
  endpoint: "income",
  kicker: "Money in",
  title: "Income",
  singular: "Income",
  description: "Load pay is added here automatically when you log a load. Use this for any other income too.",
  defaults: () => ({ date: today() }),
  fields: [
    { name: "date", label: "Date", type: "date", required: true },
    { name: "amount", label: "Amount ($)", type: "number", required: true },
    { name: "source", label: "Source", required: true, full: true, placeholder: "e.g. Load pay, convoy bonus" },
    { name: "driver_id", label: "Driver", type: "select", lookup: "drivers" },
    { name: "truck_id", label: "Truck", type: "select", lookup: "trucks" },
    { name: "notes", label: "Notes", type: "textarea", full: true },
  ],
  columns: [
    { key: "date", label: "Date", mono: true },
    { key: "source", label: "Source", render: (r) => <>{r.source}{r.load_id && <span className="ml-2 rounded bg-amber-500/10 px-1.5 font-mono text-[9px] uppercase text-amber-400">load</span>}</> },
    { key: "driver_name", label: "Driver" },
    { key: "truck_number", label: "Truck", mono: true, render: (r) => (r.truck_number ? `#${r.truck_number}` : "—") },
    { key: "amount", label: "Amount", right: true, render: (r) => <span className="text-emerald-400">{money(r.amount)}</span> },
  ],
};

export default function Income() {
  return (
    <CrudPage cfg={cfg}>
      {(items) => (
        <div className="mb-6 font-mono text-sm text-slate-400" data-testid="income-total">
          Total income: <span className="text-emerald-400">{money(items.reduce((a, b) => a + b.amount, 0))}</span>
        </div>
      )}
    </CrudPage>
  );
}
