import { useState } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { api, errMsg } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export const UserEditor = ({ target, onClose, onSaved }) => {
  const { user, logout } = useAuth();
  const [role, setRole] = useState(target.role);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const save = async (e) => {
    e.preventDefault();
    if (password !== confirm) return setError("Passwords don't match");
    if (!password && role === target.role) return setError("No changes to save");
    setBusy(true); setError("");
    try {
      await api.patch(`/users/${target.id}`, { ...(role !== target.role ? { role } : {}), ...(password ? { password } : {}) });
      toast.success(password ? "Password reset. Previous sessions signed out." : "Role updated. Previous sessions signed out.");
      onClose();
      if (target.id === user.id) await logout();
      else onSaved();
    } catch (err) { setError(errMsg(err)); } finally { setBusy(false); }
  };
  return <Dialog open onOpenChange={(open) => !open && !busy && onClose()}>
    <DialogContent data-testid="edit-user-dialog" className="bg-card border-border">
      <DialogHeader><DialogTitle>Edit {target.username}</DialogTitle><DialogDescription>Account changes sign this user out of existing sessions.</DialogDescription></DialogHeader>
      <form onSubmit={save} className="space-y-4">
        <div><Label htmlFor="edit-role">Role</Label><select id="edit-role" data-testid="edit-user-role" className="form-select mt-2" value={role} disabled={target.id === user.id} onChange={(e) => setRole(e.target.value)}><option value="dispatcher">Dispatcher</option><option value="owner">Owner</option></select></div>
        <div><Label htmlFor="edit-password">New password (optional)</Label><Input id="edit-password" data-testid="edit-user-password" autoComplete="new-password" className="mt-2" type="password" minLength={6} maxLength={72} value={password} onChange={(e) => setPassword(e.target.value)} /></div>
        <div><Label htmlFor="edit-confirm">Confirm new password</Label><Input id="edit-confirm" data-testid="edit-user-confirm" autoComplete="new-password" className="mt-2" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} /></div>
        {error && <p role="alert" data-testid="edit-user-error" className="text-sm text-destructive">{error}</p>}
        <div className="flex justify-end gap-2"><Button type="button" variant="outline" data-testid="edit-user-cancel" disabled={busy} onClick={onClose}>Cancel</Button><Button data-testid="edit-user-save" disabled={busy}>{busy ? "Saving…" : "Save changes"}</Button></div>
      </form>
    </DialogContent>
  </Dialog>;
};