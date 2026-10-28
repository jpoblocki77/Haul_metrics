import { useState } from "react";
import { Navigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/context/AuthContext";
import { errMsg } from "@/lib/api";

const HERO = "https://images.unsplash.com/photo-1592805144716-feeccccef5ac?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600";

export default function Login() {
  const { user, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(username, password);
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid min-h-screen bg-[#0B0F17] lg:grid-cols-[1.2fr_1fr]">
      <div className="relative hidden overflow-hidden lg:block">
        <img src={HERO} alt="Semi truck on highway at sunset" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#0B0F17]/30 to-[#0B0F17]" />
        <div className="absolute bottom-12 left-12 max-w-md">
          <div className="font-mono text-xs uppercase tracking-[0.3em] text-red-500">Dispatch · Books · Safety</div>
          <p className="mt-3 font-heading text-4xl font-black leading-tight text-white">Every mile, every dollar, every driver.</p>
        </div>
      </div>
      <div className="flex items-center justify-center px-6">
        <form onSubmit={submit} className="w-full max-w-sm animate-rise" data-testid="login-form">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-red-500">Virtual Trucking Co.</div>
          <h1 className="font-heading text-4xl font-black tracking-tight text-white">McCOY<span className="text-red-500">/</span>TRUCKING</h1>
          <p className="mb-10 mt-2 text-sm text-slate-400">Sign in to the McCoy Trucking office.</p>
          <div className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="username" className="font-mono text-[11px] uppercase tracking-wider text-slate-400">Username</Label>
              <Input id="username" data-testid="login-username-input" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" className="h-11 border-slate-700 bg-[#111827] text-white" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password" className="font-mono text-[11px] uppercase tracking-wider text-slate-400">Password</Label>
              <Input id="password" type="password" data-testid="login-password-input" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" className="h-11 border-slate-700 bg-[#111827] text-white" />
            </div>
            {error && <div data-testid="login-error" className="rounded border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-400">{error}</div>}
            <Button type="submit" disabled={busy} data-testid="login-submit-btn" className="h-11 w-full bg-blue-600 font-semibold text-white hover:bg-blue-500">
              {busy ? "Signing in…" : "Sign in"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
