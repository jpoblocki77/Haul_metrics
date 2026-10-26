import { useState } from "react";
import { Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/Bits";
import { api, errMsg } from "@/lib/api";

function CategoryRow({ cat, onDone }) {
  const [edit, setEdit] = useState(false);
  const [name, setName] = useState(cat.name);
  const save = async () => {
    try {
      await api.put(`/categories/${cat.id}`, { name });
      setEdit(false);
      onDone();
    } catch (e) {
      toast.error(errMsg(e));
    }
  };
  const remove = async () => {
    if (!window.confirm(`Remove category "${cat.name}"? Expenses using it become Uncategorized.`)) return;
    await api.delete(`/categories/${cat.id}`);
    toast.success("Category removed");
    onDone();
  };
  return (
    <div data-testid={`category-${cat.id}`} className="group flex items-center gap-1 rounded-full border border-slate-700 bg-[#0B0F17] py-1 pl-3 pr-1 text-sm">
      {edit ? (
        <>
          <input data-testid={`category-edit-input-${cat.id}`} value={name} onChange={(e) => setName(e.target.value)} className="w-28 bg-transparent outline-none" autoFocus />
          <button data-testid={`category-save-${cat.id}`} onClick={save} className="p-1 text-emerald-400"><Check className="h-3.5 w-3.5" /></button>
          <button onClick={() => setEdit(false)} className="p-1 text-slate-500"><X className="h-3.5 w-3.5" /></button>
        </>
      ) : (
        <>
          <span>{cat.name}</span>
          <button data-testid={`category-rename-${cat.id}`} onClick={() => setEdit(true)} className="p-1 text-slate-500 hover:text-amber-400"><Pencil className="h-3 w-3" /></button>
          <button data-testid={`category-delete-${cat.id}`} onClick={remove} className="p-1 text-slate-500 hover:text-rose-400"><Trash2 className="h-3 w-3" /></button>
        </>
      )}
    </div>
  );
}

export default function CategoryManager({ categories, onChange }) {
  const [name, setName] = useState("");
  const add = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await api.post("/categories", { name: name.trim() });
      setName("");
      toast.success("Category added");
      onChange();
    } catch (err) {
      toast.error(errMsg(err));
    }
  };
  return (
    <Panel title="Expense categories" testId="category-manager" className="mb-6">
      <div className="flex flex-wrap items-center gap-2">
        {categories.map((c) => <CategoryRow key={c.id} cat={c} onDone={onChange} />)}
        <form onSubmit={add} className="flex items-center gap-2">
          <Input data-testid="new-category-input" value={name} onChange={(e) => setName(e.target.value)} placeholder="New category" className="h-8 w-40 border-slate-700 bg-[#0B0F17]" />
          <Button data-testid="add-category-btn" type="submit" size="sm" variant="outline" className="h-8 border-amber-500/40 bg-transparent text-amber-400 hover:bg-amber-500/10 hover:text-amber-300">
            <Plus className="h-3.5 w-3.5" /> Add
          </Button>
        </form>
      </div>
    </Panel>
  );
}
