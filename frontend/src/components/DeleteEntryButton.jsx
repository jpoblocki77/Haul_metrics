import { useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel } from "@/components/ui/alert-dialog";
import { useAuth } from "@/context/AuthContext";
import { api, errMsg } from "@/lib/api";

const WARNINGS = {
  loads: "The load and its linked income will be deleted.",
  drivers: "Past records stay, but will no longer be linked to this driver.",
  trucks: "Past records stay, but will no longer be linked to this truck.",
  categories: "Expenses stay and become uncategorized.",
  "telemetry/events": "Only this detection is deleted. Any approved load, income or fuel entry stays.",
  users: "This account will no longer be able to sign in.",
};

export const DeleteEntryButton = ({ table, row, label, testId, onDeleted }) => {
  const { isOwner } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (!isOwner) return null;
  const remove = async () => {
    setBusy(true); setError("");
    try {
      await api.delete(`/${table}/${row.id}`);
      setOpen(false); toast.success("Entry deleted");
      window.dispatchEvent(new Event("company-records-changed")); onDeleted?.();
    } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };
  return <><button type="button" title={`Delete ${label}`} aria-label={`Delete ${label}`} data-testid={testId} onClick={() => { setError(""); setOpen(true); }} className="shrink-0 rounded p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"><Trash2 size={16} /></button>
    <AlertDialog open={open} onOpenChange={(v) => !busy && setOpen(v)}><AlertDialogContent data-testid={`${testId}-dialog`} className="max-h-[90vh] overflow-y-auto bg-card"><AlertDialogHeader><AlertDialogTitle>Delete this entry?</AlertDialogTitle><AlertDialogDescription className="break-words" data-testid={`${testId}-description`}><span className="mb-2 block font-semibold text-foreground">{label}</span>{WARNINGS[table] || "This permanently removes the selected entry."} This cannot be undone without restoring a backup.</AlertDialogDescription></AlertDialogHeader>
      {error && <p role="alert" data-testid={`${testId}-error`} className="text-sm text-destructive">{error}</p>}
      <AlertDialogFooter><AlertDialogCancel data-testid={`${testId}-cancel`} disabled={busy}>Cancel</AlertDialogCancel><Button data-testid={`${testId}-confirm`} variant="destructive" disabled={busy} onClick={remove}>{busy ? "Deleting…" : "Delete entry"}</Button></AlertDialogFooter>
    </AlertDialogContent></AlertDialog>
  </>;
};