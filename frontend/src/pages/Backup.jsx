import { useState } from "react";
import { Download, Upload, LockKeyhole, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/Bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { api, errMsg } from "@/lib/api";
import { downloadBlob, fileBase64 } from "@/lib/download";
import { useAuth } from "@/context/AuthContext";
import { EraseRecords } from "@/components/EraseRecords";

export default function Backup() {
  const { logout } = useAuth();
  const [pass, setPass] = useState("");
  const [repeat, setRepeat] = useState("");
  const [restorePass, setRestorePass] = useState("");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [confirm, setConfirm] = useState("");
  const [ownerPassword, setOwnerPassword] = useState("");
  const exportBackup = async (e) => {
    e.preventDefault(); setError("");
    if (pass !== repeat) return setError("Backup passwords don't match");
    setBusy("export");
    try { const r = await api.post("/backup/export", { passphrase: pass }, { responseType: "blob" }); downloadBlob(r.data, `mccoy-company-${new Date().toISOString().slice(0,10)}.mccoy`); toast.success("Encrypted backup downloaded"); }
    catch (e) { let message = errMsg(e); if (e.response?.data instanceof Blob) { try { message = JSON.parse(await e.response.data.text()).detail; } catch {} } setError(message); }
    finally { setBusy(""); }
  };
  const inspect = async (e) => {
    e.preventDefault(); setError(""); setPreview(null);
    if (!file) return setError("Choose a McCoy backup file");
    if (file.size > 18 * 1024 * 1024) return setError("Backup must be smaller than 18 MB");
    setBusy("inspect");
    try { const archive = await fileBase64(file); const { data } = await api.post("/backup/inspect", { archive, passphrase: restorePass }); setPreview({ ...data, archive }); setConfirm(""); setOwnerPassword(""); }
    catch (e) { setError(errMsg(e)); } finally { setBusy(""); }
  };
  const restore = async (e) => {
    e.preventDefault(); setBusy("restore"); setError("");
    try { await api.post("/backup/restore", { archive: preview.archive, passphrase: restorePass, confirm, owner_password: ownerPassword }); toast.success("Company restored. Sign in with an account from the backup."); await logout(); }
    catch (e) { setError(errMsg(e)); } finally { setBusy(""); }
  };
  return <div data-testid="backup-page">
    <PageHeader kicker="Company records" title="Backup & restore" />
    <div data-testid="backup-security-note" className="mb-8 flex gap-3 border-y border-border py-5 text-sm text-muted-foreground"><LockKeyhole className="shrink-0 text-primary" /><p>Encrypted company archive: records, accounts, categories and telemetry review history. Keep the backup password safe; it cannot be recovered. Live telemetry connections are disabled after restore.</p></div>
    {error && !preview && <p role="alert" data-testid="backup-error" className="mb-5 text-sm text-destructive">{error}</p>}
    <div className="grid gap-12 lg:grid-cols-2">
      <section className="min-w-0"><h2 className="mb-5 flex items-center gap-2 font-heading text-lg font-bold"><Download size={20} className="text-primary" />Back up company</h2><form className="space-y-4" onSubmit={exportBackup}>
        <div><Label htmlFor="backup-password">Backup password · at least 12 characters</Label><Input id="backup-password" data-testid="backup-password" className="mt-2" required minLength={12} maxLength={256} type="password" autoComplete="new-password" value={pass} onChange={(e) => setPass(e.target.value)} /></div>
        <div><Label htmlFor="backup-repeat">Confirm backup password</Label><Input id="backup-repeat" data-testid="backup-repeat" className="mt-2" required type="password" autoComplete="new-password" value={repeat} onChange={(e) => setRepeat(e.target.value)} /></div>
        <Button data-testid="backup-download" disabled={!!busy}><Download size={16} className="mr-2" />{busy === "export" ? "Encrypting…" : "Download backup"}</Button>
      </form></section>
      <section className="min-w-0"><h2 className="mb-5 flex items-center gap-2 font-heading text-lg font-bold"><Upload size={20} className="text-primary" />Restore company</h2><form className="space-y-4" onSubmit={inspect}>
        <div><Label htmlFor="restore-file">McCoy backup file</Label><Input id="restore-file" data-testid="restore-file" className="mt-2 cursor-pointer" type="file" accept=".mccoy" required onChange={(e) => { setFile(e.target.files[0] || null); setPreview(null); }} /></div>
        <div><Label htmlFor="restore-password">Backup password</Label><Input id="restore-password" data-testid="restore-password" className="mt-2" type="password" minLength={12} required value={restorePass} onChange={(e) => { setRestorePass(e.target.value); setPreview(null); }} /></div>
        <p data-testid="restore-warning" className="flex gap-2 text-sm text-destructive"><ShieldAlert size={18} className="shrink-0" />Restore replaces this company's records and accounts. Download a current backup first.</p>
        <Button data-testid="backup-inspect" variant="outline" disabled={!!busy}>{busy === "inspect" ? "Checking…" : "Preview restore"}</Button>
      </form></section>
    </div>
    <Dialog open={!!preview} onOpenChange={(open) => !open && !busy && setPreview(null)}><DialogContent data-testid="restore-dialog" className="max-h-[90vh] overflow-y-auto bg-card"><DialogHeader><DialogTitle>Replace company records?</DialogTitle><DialogDescription>All current sessions will be signed out. Use an account from this backup afterward.</DialogDescription></DialogHeader>
      {preview && <form onSubmit={restore} className="space-y-4"><p data-testid="restore-archive-date" className="text-xs text-muted-foreground">Backup from {new Date(preview.created_at).toLocaleString()}</p><div data-testid="restore-counts" className="grid grid-cols-2 gap-2 text-sm">{Object.entries(preview.counts).filter(([k]) => !k.startsWith("telemetry_sources")).map(([key, n]) => <div key={key} className="flex justify-between gap-3 border-b border-border py-1"><span className="break-words">{key.replaceAll("_", " ")}</span><span className="font-mono">{n}</span></div>)}</div><p data-testid="restore-owner-list" className="break-words text-sm">Restored owners: {preview.owners.join(", ")}</p>
        <div><Label htmlFor="restore-owner-password">Your current owner password</Label><Input id="restore-owner-password" data-testid="restore-owner-password" type="password" className="mt-2" required value={ownerPassword} onChange={(e) => setOwnerPassword(e.target.value)} /></div>
        <div><Label htmlFor="restore-confirmation">Type RESTORE MCCOY to confirm replacement</Label><Input id="restore-confirmation" data-testid="restore-confirmation" className="mt-2" value={confirm} onChange={(e) => setConfirm(e.target.value)} /></div>
        {error && <p role="alert" data-testid="restore-error" className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end gap-2"><Button type="button" variant="outline" data-testid="restore-cancel" disabled={!!busy} onClick={() => setPreview(null)}>Cancel</Button><Button data-testid="backup-restore" variant="destructive" disabled={!!busy || confirm !== "RESTORE MCCOY" || !ownerPassword}>{busy === "restore" ? "Restoring…" : "Replace & restore"}</Button></div>
      </form>}
    </DialogContent></Dialog>
    <EraseRecords />
  </div>;
}