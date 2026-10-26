import { useState } from "react";
import CrudPage from "@/components/CrudPage";
import CategoryManager from "@/pages/CategoryManager";
import { useFetch } from "@/hooks/useData";
import { money, today } from "@/lib/api";

const cfg = {
  endpoint: "expenses",
  kicker: "Money out",
  title: "Expenses",
  singular: "Expense",
  description: "Fuel purchases and DOT fines are tracked on their own pages and added to total expenses automatically.",
  defaults: () => ({ date: today() }),
  fields: [
    { name: "date", label: "Date", type: "date", required: true },
    { name: "amount", label: "Amount ($)", type: "number", required: true },
    { name: "category_id", label: "Category", type: "select", lookup: "categories" },
    { name: "driver_id", label: "Driver", type: "select", lookup: "drivers" },
    { name: "truck_id", label: "Truck", type: "select", lookup: "trucks" },
    { name: "description", label: "Description", full: true },
  ],
  columns: [
    { key: "date", label: "Date", mono: true },
    { key: "category_name", label: "Category", render: (r) => r.category_name || <span className="text-slate-500">Uncategorized</span> },
    { key: "description", label: "Description" },
    { key: "driver_name", label: "Driver" },
    { key: "truck_number", label: "Truck", mono: true, render: (r) => (r.truck_number ? `#${r.truck_number}` : "—") },
    { key: "amount", label: "Amount", right: true, render: (r) => <span className="text-rose-400">{money(r.amount)}</span> },
  ],
};

export default function Expenses() {
  const [cats, reloadCats] = useFetch("/categories");
  const [catFilter, setCatFilter] = useState("all");
  const [key, setKey] = useState(0);
  if (cats && catFilter !== "all" && !cats.some((c) => String(c.id) === catFilter)) setCatFilter("all");
  const filter = catFilter === "all" ? null : (r) => String(r.category_id) === catFilter;
  const toolbar = (
    <select data-testid="expenses-category-filter" value={catFilter} onChange={(e) => setCatFilter(e.target.value)} className="h-9 rounded-md border border-slate-700 bg-[#0B0F17] px-3 text-sm">
      <option value="all">All categories</option>
      {(cats || []).map((c) => <option key={c.id} value={String(c.id)}>{c.name}</option>)}
    </select>
  );
  return (
    <CrudPage key={key} cfg={{ ...cfg, toolbar }} filter={filter}>
      {(items) => (
        <>
          <CategoryManager categories={cats || []} onChange={() => reloadCats().then(() => setKey((k) => k + 1))} />
          <div className="mb-6 font-mono text-sm text-slate-400" data-testid="expenses-total">
            Shown total: <span className="text-rose-400">{money(items.filter(filter || (() => true)).reduce((a, b) => a + b.amount, 0))}</span>
          </div>
        </>
      )}
    </CrudPage>
  );
}
