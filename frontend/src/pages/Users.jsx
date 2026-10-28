import { useState } from "react";
import { Trash2, UserPlus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PageHeader, Panel } from "@/components/Bits";
import { useFetch } from "@/hooks/useData";
import { useAuth } from "@/context/AuthContext";
import { api, errMsg } from "@/lib/api";

export default function Users() {
  const { user } = useAuth();
  const [users, reload] = useFetch("/users");
  const [form, setForm] = useState({ username: "", password: "", confirm: "", role: "dispatcher" });
  const [busy, setBusy] = useState(false);

  const create = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) return toast.error("Passwords don't match");
    if (!/^[A-Za-z0-9_.-]{3,32}$/.test(form.username)) return toast.error("Username must be 3–32 letters, numbers, dot, dash or underscore");
    if (form.password.length < 6) return toast.error("Password must be at least 6 characters");
    setBusy(true);
    try {
      await api.post("/users", { username: form.username, password: form.password, role: form.role });
      toast.success(`User ${form.username} created`);
      setForm({ username: "", password: "", confirm: "", role: "dispatcher" });
      reload();
    } catch (err) {
      toast.error(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (u) => {
    if (!window.confirm(`Remove user "${u.username}"?`)) return;
    try {
      await api.delete(`/users/${u.id}`);
      toast.success("User removed");
      reload();
    } catch (err) {
      toast.error(errMsg(err));
    }
  };

  const field = (name, label, type = "text") => (
    <div className="space-y-1.5">
      <Label htmlFor={`user-${name}`} className="font-mono text-[11px] uppercase tracking-wider text-slate-400">{label}</Label>
      <Input id={`user-${name}`} data-testid={`new-user-${name}`} type={type} value={form[name]} onChange={(e) => setForm({ ...form, [name]: e.target.value })} className="border-slate-700 bg-[#0B0F17]" />
    </div>
  );

  return (
    <div data-testid="users-page">
      <PageHeader kicker="Office access" title="Users" />
      <div className="grid gap-6 lg:grid-cols-[1fr_1.3fr]">
        <Panel title="Create a user">
          <form onSubmit={create} className="space-y-4">
            {field("username", "Username")}
            {field("password", "Password", "password")}
            {field("confirm", "Confirm password", "password")}
            <div className="space-y-1.5">
              <div className="font-mono text-[11px] uppercase tracking-wider text-slate-400">Role</div>
              <div className="grid grid-cols-2 gap-2" data-testid="new-user-role">
                {[["dispatcher", "Dispatcher", "Logs and edits records. Can't delete data or manage users."], ["owner", "Owner", "Full control, including users and deleting data."]].map(([v, l, d]) => (
                  <button type="button" key={v} data-testid={`new-user-role-${v}`} onClick={() => setForm({ ...form, role: v })}
                    className={`rounded-md border p-3 text-left transition-colors ${form.role === v ? "border-blue-500 bg-blue-500/10" : "border-slate-700 hover:border-slate-500"}`}>
                    <div className="text-sm font-semibold">{l}</div>
                    <div className="mt-1 text-[11px] text-slate-500">{d}</div>
                  </button>
                ))}
              </div>
            </div>
            <p className="text-[11px] text-slate-500">3–32 letters, numbers, dot, dash or underscore. Password at least 6 characters.</p>
            <Button data-testid="create-user-btn" disabled={busy} type="submit" className="bg-blue-600 font-semibold text-white hover:bg-blue-500">
              <UserPlus className="mr-2 h-4 w-4" /> Create user
            </Button>
          </form>
        </Panel>
        <Panel title="Everyone with access">
          <div className="space-y-2">
            {(users || []).map((u) => (
              <div key={u.id} data-testid={`user-row-${u.username}`} className="flex items-center gap-3 rounded-md bg-[#0B0F17] px-4 py-3">
                <span className="flex-1 font-mono text-sm">{u.username}<span className={`ml-2 rounded px-1.5 py-0.5 text-[10px] uppercase ${u.role === "owner" ? "bg-red-500/10 text-red-400" : "bg-blue-500/10 text-blue-400"}`} data-testid={`user-role-${u.username}`}>{u.role}</span>{u.id === user?.id && <span className="ml-2 text-[10px] uppercase text-blue-400">you</span>}</span>
                <span className="font-mono text-xs text-slate-500">{u.created_at?.slice(0, 10)}</span>
                {u.id !== user?.id && (
                  <button data-testid={`delete-user-${u.username}`} onClick={() => remove(u)} className="rounded p-1.5 text-slate-500 hover:bg-slate-700 hover:text-rose-400"><Trash2 className="h-4 w-4" /></button>
                )}
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
