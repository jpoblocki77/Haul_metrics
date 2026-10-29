import { useEffect, useState } from "react";
import { Save, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/Bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCompany } from "@/context/CompanyContext";
import { api, errMsg } from "@/lib/api";
import { DEFAULT_BRANDING, contrastText, inkColor } from "@/lib/branding";

const colors = [["primary_color", "Main color"], ["accent_color", "Accent color"], ["dark_background", "Dark mode background"], ["light_background", "Light mode background"]];
export default function CompanySettings() {
  const { company, setCompany } = useCompany();
  const [form, setForm] = useState(company);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => setForm(company), [company]);
  const update = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const save = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try { const { data } = await api.put("/company/branding", form); setCompany(data); setForm(data); toast.success("Company branding saved"); }
    catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };
  return <div data-testid="company-settings-page"><PageHeader kicker="Owner settings" title="Company & colors" />
    <div className="grid min-w-0 gap-10 lg:grid-cols-[1fr_1fr]">
      <form onSubmit={save} className="min-w-0 space-y-6 border-y border-border py-6">
        <div><Label htmlFor="company-name">Company name</Label><Input id="company-name" data-testid="company-name-input" required maxLength={60} value={form.company_name} onChange={(e) => update("company_name", e.target.value)} className="mt-2" /></div>
        <div className="grid gap-5 sm:grid-cols-2">{colors.map(([key, label]) => <div key={key}><Label htmlFor={`company-${key}`}>{label}</Label><div className="mt-2 flex items-center gap-3"><input id={`company-${key}`} data-testid={`company-${key.replaceAll("_", "-")}`} type="color" value={form[key]} onChange={(e) => update(key, e.target.value)} className="h-11 w-14 shrink-0 cursor-pointer rounded border border-border bg-background p-1" /><span data-testid={`company-${key}-value`} className="font-mono text-xs uppercase text-muted-foreground">{form[key]}</span></div></div>)}</div>
        <p className="text-xs text-muted-foreground">Dark backgrounds must stay dark and light backgrounds must stay light for readable text. Name and colors apply company-wide.</p>
        {error && <p role="alert" data-testid="company-settings-error" className="text-sm text-destructive">{error}</p>}
        <div className="flex flex-wrap gap-3"><Button data-testid="company-save" disabled={busy}><Save size={16} className="mr-2" />{busy ? "Saving…" : "Save company"}</Button><Button type="button" variant="outline" data-testid="company-reset-colors" onClick={() => setForm({ ...DEFAULT_BRANDING, company_name: form.company_name })} disabled={busy}><RotateCcw size={16} className="mr-2" />Default colors</Button></div>
      </form>
      <section className="min-w-0"><h2 className="mb-4 font-heading text-lg font-bold">Preview</h2><div className="space-y-4">{["dark", "light"].map((theme) => { const background = form[`${theme}_background`]; return <div key={theme} data-testid={`company-preview-${theme}`} className="min-w-0 rounded-lg border border-border p-6" style={{ background, color: contrastText(background) }}><div className="text-xs uppercase opacity-70">{theme} mode</div><div className="mt-4 break-words font-heading text-2xl font-bold">{form.company_name || "Company name"}</div><div className="mt-3 h-1 w-16" style={{ background: form.accent_color }} /><div className="mt-5 font-mono text-xl" style={{ color: inkColor(form.primary_color, theme === "dark") }}>$12,450.00</div><div className="mt-4 inline-flex rounded-md px-4 py-2 text-sm font-semibold" style={{ background: form.primary_color, color: contrastText(form.primary_color) }}>Main color</div></div>; })}</div></section>
    </div>
  </div>;
}