import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, UserPlus, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/Bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, errMsg } from "@/lib/api";

export default function CreateUser() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "", confirm: "", role: "dispatcher" });
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (key, value) => { setForm((f) => ({ ...f, [key]: value })); setError(""); };
  const create = async (e) => {
    e.preventDefault(); setError("");
    if (form.password !== form.confirm) return setError("Passwords don't match. Please enter the same password twice.");
    setBusy(true);
    try {
      const { data } = await api.post("/users", { username: form.username.trim(), password: form.password, role: form.role });
      toast.success(`${data.username} created — ready to sign in`);
      navigate("/users", { state: { created: data.username } });
    } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };
  return <div data-testid="create-user-page" className="max-w-2xl">
    <Link data-testid="create-user-back" to="/users" className="mb-5 inline-flex items-center gap-2 text-sm text-primary"><ArrowLeft size={16} /> Users</Link>
    <PageHeader kicker="Office access" title="Create user" />
    <form data-testid="create-user-form" onSubmit={create} className="space-y-6 border-y border-border py-6">
      <div><Label htmlFor="new-username">Username</Label><Input id="new-username" data-testid="new-user-username" className="mt-2" autoComplete="off" required minLength={3} maxLength={32} pattern="[A-Za-z0-9_.\-]+" placeholder="e.g. dispatch2" value={form.username} onChange={(e) => set("username", e.target.value)} /><p className="mt-2 text-xs text-muted-foreground">3–32 letters, numbers, dots, dashes or underscores.</p></div>
      <div><Label htmlFor="new-password">Password</Label><div className="relative mt-2"><Input id="new-password" data-testid="new-user-password" className="pr-12" autoComplete="new-password" required minLength={6} maxLength={72} type={show ? "text" : "password"} value={form.password} onChange={(e) => set("password", e.target.value)} /><button type="button" data-testid="new-user-toggle-password" title={show ? "Hide password" : "Show password"} aria-label={show ? "Hide password" : "Show password"} onClick={() => setShow(!show)} className="absolute right-3 top-2.5 text-muted-foreground transition-colors hover:text-primary">{show ? <EyeOff size={18} /> : <Eye size={18} />}</button></div><p className="mt-2 text-xs text-muted-foreground">At least 6 characters. Share it privately with the new user.</p></div>
      <div><Label htmlFor="new-confirm">Confirm password</Label><Input id="new-confirm" data-testid="new-user-confirm" className="mt-2" autoComplete="new-password" required type={show ? "text" : "password"} value={form.confirm} onChange={(e) => set("confirm", e.target.value)} /></div>
      <div><Label htmlFor="new-role">Role</Label><select id="new-role" data-testid="new-user-role" className="form-select mt-2" value={form.role} onChange={(e) => set("role", e.target.value)}><option value="dispatcher">Dispatcher</option><option value="owner">Owner</option></select><p data-testid="new-user-role-description" className="mt-2 text-xs text-muted-foreground">{form.role === "dispatcher" ? "Can add and edit records. Cannot delete data or manage users." : "Full access, including accounts, deleting records and restoring backups."}</p></div>
      {error && <p data-testid="create-user-error" role="alert" className="text-sm text-destructive">{error}</p>}
      <div className="flex flex-wrap gap-3"><Button type="submit" data-testid="create-user-btn" disabled={busy}><UserPlus className="mr-2 h-4 w-4" />{busy ? "Creating…" : "Create user"}</Button><Button type="button" variant="outline" data-testid="create-user-cancel" disabled={busy} onClick={() => navigate("/users")}>Cancel</Button></div>
    </form>
  </div>;
}