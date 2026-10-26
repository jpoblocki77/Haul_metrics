import { useMemo, useState } from "react";
import { Plus, Pencil, Trash2, Search } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import FieldInput from "@/components/FieldInput";
import { PageHeader, TestTag } from "@/components/Bits";
import { api, errMsg } from "@/lib/api";
import { useFetch, useLookups } from "@/hooks/useData";

function toPayload(fields, form) {
  const out = {};
  fields.forEach((f) => {
    let v = form[f.name];
    if (v === "" || v === undefined) v = null;
    if (v != null && (f.type === "number" || f.lookup)) v = Number(v);
    out[f.name] = v;
  });
  return out;
}

export default function CrudPage({ cfg, children, filter, onChanged }) {
  const [items, reload] = useFetch(`/${cfg.endpoint}`);
  const lookups = useLookups();
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({});
  const [toDelete, setToDelete] = useState(null);
  const [q, setQ] = useState("");
  const [saving, setSaving] = useState(false);

  const fields = typeof cfg.fields === "function" ? cfg.fields(form) : cfg.fields;
  const allFields = typeof cfg.fields === "function" ? cfg.fields({ ...form, __all: true }) : cfg.fields;

  const rows = useMemo(() => {
    let r = items || [];
    if (filter) r = r.filter(filter);
    if (q) r = r.filter((x) => JSON.stringify(x).toLowerCase().includes(q.toLowerCase()));
    return r;
  }, [items, q, filter]);

  const openNew = () => {
    setForm(cfg.defaults ? cfg.defaults() : {});
    setEditing("new");
  };
  const openEdit = (row) => {
    const f = {};
    allFields.forEach((fd) => (f[fd.name] = row[fd.name] == null ? "" : String(row[fd.name])));
    setForm(f);
    setEditing(row);
  };
  const setField = (name, value) => {
    setForm((prev) => {
      const next = { ...prev, [name]: value };
      return cfg.onFieldChange ? cfg.onFieldChange(name, value, next, lookups) : next;
    });
  };

  const save = async () => {
    setSaving(true);
    try {
      const payload = toPayload(allFields, form);
      if (editing === "new") await api.post(`/${cfg.endpoint}`, payload);
      else await api.put(`/${cfg.endpoint}/${editing.id}`, payload);
      toast.success(`${cfg.singular} saved`);
      setEditing(null);
      await reload();
      onChanged?.();
      if (cfg.reloadLookups) lookups.reload();
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setSaving(false);
    }
  };

  const doDelete = async () => {
    try {
      await api.delete(`/${cfg.endpoint}/${toDelete.id}`);
      toast.success(`${cfg.singular} removed`);
      setToDelete(null);
      await reload();
      onChanged?.();
    } catch (e) {
      toast.error(errMsg(e));
    }
  };

  const slug = cfg.endpoint;
  return (
    <div data-testid={`${slug}-page`}>
      <PageHeader kicker={cfg.kicker} title={cfg.title}>
        <Button data-testid={`add-${slug}-btn`} onClick={openNew} className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
          <Plus className="mr-1 h-4 w-4" /> Add {cfg.singular}
        </Button>
      </PageHeader>

      {typeof children === "function" ? children(items || []) : children}

      <div className="animate-rise rounded-lg border border-slate-800 bg-[#111827]">
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-800 p-4">
          <div className="relative w-full max-w-xs">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input data-testid={`${slug}-search`} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search…" className="border-slate-700 bg-[#0B0F17] pl-9" />
          </div>
          {cfg.toolbar}
          <div className="ml-auto font-mono text-xs text-slate-500" data-testid={`${slug}-count`}>{rows.length} records</div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid={`${slug}-table`}>
            <thead>
              <tr className="border-b border-slate-800 text-left">
                {cfg.columns.map((c) => (
                  <th key={c.key} className={`whitespace-nowrap px-4 py-3 font-mono text-[10px] font-medium uppercase tracking-[0.15em] text-slate-500 ${c.right ? "text-right" : ""}`}>{c.label}</th>
                ))}
                <th className="w-24 px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {items === null && (
                <tr><td colSpan={99} className="px-4 py-10 text-center text-slate-500">Loading…</td></tr>
              )}
              {items && rows.length === 0 && (
                <tr><td colSpan={99} className="px-4 py-12 text-center text-slate-500" data-testid={`${slug}-empty`}>No records yet. Add one, or load sample data from Test Data.</td></tr>
              )}
              {rows.map((r, i) => (
                <tr key={r.id} data-testid={`${slug}-row-${r.id}`} className="border-b border-slate-800/60 transition-colors hover:bg-slate-800/30">
                  {cfg.columns.map((c, ci) => (
                    <td key={c.key} className={`whitespace-nowrap px-4 py-3 ${c.right ? "text-right font-mono tabular-nums" : ""} ${c.mono ? "font-mono" : ""}`}>
                      {c.render ? c.render(r) : r[c.key] ?? "—"}
                      {ci === 0 && <TestTag row={r} />}
                    </td>
                  ))}
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <button data-testid={`edit-${slug}-${r.id}`} onClick={() => openEdit(r)} className="rounded p-1.5 text-slate-500 transition-colors hover:bg-slate-700 hover:text-amber-400"><Pencil className="h-4 w-4" /></button>
                    <button data-testid={`delete-${slug}-${r.id}`} onClick={() => setToDelete(r)} className="rounded p-1.5 text-slate-500 transition-colors hover:bg-slate-700 hover:text-rose-400"><Trash2 className="h-4 w-4" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogContent data-testid={`${slug}-dialog`} className="max-h-[90vh] overflow-y-auto border-slate-700 bg-[#111827] text-slate-100 sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl">{editing === "new" ? "New" : "Edit"} {cfg.singular}</DialogTitle>
            <DialogDescription className="text-slate-500">{cfg.description}</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            {fields.map((f) => (
              <FieldInput key={f.name} field={f} value={form[f.name]} onChange={(v) => setField(f.name, v)} lookups={lookups} />
            ))}
          </div>
          {cfg.preview && cfg.preview(form, lookups)}
          <DialogFooter>
            <Button variant="ghost" data-testid={`${slug}-cancel-btn`} onClick={() => setEditing(null)} className="text-slate-400 hover:bg-slate-800 hover:text-white">Cancel</Button>
            <Button data-testid={`${slug}-save-btn`} disabled={saving} onClick={save} className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
              {saving ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!toDelete} onOpenChange={(o) => !o && setToDelete(null)}>
        <AlertDialogContent className="border-slate-700 bg-[#111827] text-slate-100">
          <AlertDialogHeader>
            <AlertDialogTitle>Remove this {cfg.singular.toLowerCase()}?</AlertDialogTitle>
            <AlertDialogDescription className="text-slate-400">{cfg.deleteWarning || "This can't be undone."}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="confirm-delete-cancel" className="border-slate-700 bg-transparent hover:bg-slate-800 hover:text-white">Cancel</AlertDialogCancel>
            <AlertDialogAction data-testid="confirm-delete-btn" onClick={doDelete} className="bg-rose-600 hover:bg-rose-500">Remove</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
