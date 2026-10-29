import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Trash2, UserPlus, Pencil, CheckCircle2 } from "lucide-react";
import { UserEditor } from "@/components/UserEditor";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/Bits";
import { useFetch } from "@/hooks/useData";
import { useAuth } from "@/context/AuthContext";
import { api, errMsg } from "@/lib/api";

export default function Users() {
  const { user } = useAuth();
  const { state } = useLocation();
  const [users, reload, error] = useFetch("/users");
  const [editing, setEditing] = useState(null);
  const remove = async (u) => {
    if (!window.confirm(`Remove user "${u.username}"?`)) return;
    try { await api.delete(`/users/${u.id}`); toast.success("User removed"); reload(); }
    catch (err) { toast.error(errMsg(err)); }
  };
  return <div data-testid="users-page">
    <PageHeader kicker="Office access" title="Users"><Button asChild><Link data-testid="users-create-user" to="/users/new"><UserPlus className="mr-2 h-4 w-4" />Create user</Link></Button></PageHeader>
    {state?.created && <div role="status" data-testid="user-created-confirmation" className="mb-6 flex items-center gap-3 border-y border-primary/30 py-4 text-sm text-primary"><CheckCircle2 size={20} /><span className="break-all"><strong>{state.created}</strong> is ready to sign in with the password you entered.</span></div>}
    {error && <p role="alert" data-testid="users-error" className="mb-4 text-sm text-destructive">{errMsg(error)} <Button data-testid="users-retry" onClick={reload}>Retry</Button></p>}
    {!users && !error && <p data-testid="users-loading" className="text-muted-foreground">Loading users…</p>}
    <div className="max-w-4xl border-t border-border">
      {(users || []).map((u) => <div key={u.id} data-testid={`user-row-${u.username}`} className="flex flex-wrap items-center gap-3 border-b border-border py-5">
        <div className="min-w-0 flex-1"><span className="break-all font-mono text-sm font-semibold">{u.username}</span>{u.id === user?.id && <span className="ml-2 text-xs text-primary">you</span>}<div data-testid={`user-role-${u.username}`} className="mt-1 text-xs capitalize text-muted-foreground">{u.role}</div></div>
        <span data-testid={`user-created-at-${u.username}`} className="hidden text-xs text-muted-foreground sm:inline">Joined {u.created_at?.slice(0, 10)}</span>
        <Button variant="outline" data-testid={`edit-user-${u.username}`} onClick={() => setEditing(u)}><Pencil className="mr-2 h-4 w-4" />Edit</Button>
        {u.id !== user?.id && <button title={`Remove ${u.username}`} aria-label={`Remove ${u.username}`} data-testid={`delete-user-${u.username}`} onClick={() => remove(u)} className="rounded p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"><Trash2 className="h-4 w-4" /></button>}
      </div>)}
    </div>
    {editing && <UserEditor key={editing.id} target={editing} onClose={() => setEditing(null)} onSaved={reload} />}
  </div>;
}