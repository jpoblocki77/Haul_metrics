import { useState } from "react";
import { Trash2, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { api, errMsg } from "@/lib/api";

export const EraseRecords = () => {
  const [open, setOpen] = useState(false);
  const [counts, setCounts] = useState(null);
  const [confirmation, setConfirmation] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const show = async () => {
    setOpen(true); setCounts(null); setConfirmation(""); setPassword(""); setError("");
    try { setCounts((await api.get("/company/record-counts")).data); } catch (e) { setError(errMsg(e)); }
  };
  const erase = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try { await api.post("/company/erase-records", { confirmation, owner_password: password }); setOpen(false); toast.success("All company records erased. Accounts and branding were kept."); window.dispatchEvent(new Event("company-records-changed")); }
    catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };
  return <section className="mt-12 border-t border-destructive/40 pt-7" data-testid="erase-records-section"><h2 className="mb-3 flex items-center gap-2 font-heading text-lg font-bold text-destructive"><ShieldAlert size={20} />Erase company records</h2><p data-testid="erase-records-warning" className="mb-5 max-w-2xl text-sm text-muted-foreground">Permanently removes all income, expenses, fuel purchases, loads, inspections, drivers, trucks, categories and telemetry history. Accounts and company colors stay. Download a backup first.</p><Button variant="destructive" data-testid="open-erase-records" onClick={show}><Trash2 size={16} className="mr-2" />Erase all records</Button>
    <Dialog open={open} onOpenChange={(value) => !busy && setOpen(value)}><DialogContent data-testid="erase-records-dialog" className="max-h-[90vh] overflow-y-auto bg-card"><DialogHeader><DialogTitle>Erase every company record?</DialogTitle><DialogDescription>This cannot be undone without a backup. User accounts and company branding will not be removed. Telemetry connections will stop until configured again.</DialogDescription></DialogHeader>
      <form onSubmit={erase} className="space-y-4">{counts ? <div data-testid="erase-record-counts" className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">{Object.entries(counts).map(([key, count]) => <div key={key} className="flex justify-between gap-2"><span className="break-words capitalize">{key.replaceAll("_", " ")}</span><span className="font-mono">{count}</span></div>)}</div> : <p data-testid="erase-counts-loading" className="text-sm text-muted-foreground">Loading record counts…</p>}
        <div><Label htmlFor="erase-owner-password">Your current owner password</Label><Input id="erase-owner-password" data-testid="erase-owner-password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} className="mt-2" /></div>
        <div><Label htmlFor="erase-confirmation">Type ERASE ALL RECORDS to confirm</Label><Input id="erase-confirmation" data-testid="erase-confirmation" value={confirmation} onChange={(e) => setConfirmation(e.target.value)} className="mt-2" /></div>
        {error && <p role="alert" data-testid="erase-records-error" className="text-sm text-destructive">{error}</p>}
        <div className="flex flex-wrap justify-end gap-2"><Button type="button" variant="outline" data-testid="erase-records-cancel" disabled={busy} onClick={() => setOpen(false)}>Cancel</Button><Button variant="destructive" data-testid="erase-records-confirm" disabled={busy || !counts || !password || confirmation !== "ERASE ALL RECORDS"}>{busy ? "Erasing…" : "Permanently erase records"}</Button></div>
      </form>
    </DialogContent></Dialog>
  </section>;
};