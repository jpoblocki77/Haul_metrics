import { useEffect, useState } from "react";
import { Radio, Download, Fuel, PackageCheck, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/Bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useFetch, useLookups } from "@/hooks/useData";
import { api, errMsg, num } from "@/lib/api";
import { downloadBlob } from "@/lib/download";
import { TelemetryReview } from "@/components/TelemetryReview";
import { DeleteEntryButton } from "@/components/DeleteEntryButton";

export default function Telemetry() {
  const [status, reloadStatus, statusError] = useFetch("/telemetry/status");
  const [events, reloadEvents, eventsError] = useFetch("/telemetry/events");
  const { drivers, trucks } = useLookups();
  const [form, setForm] = useState({ driver_id: "", truck_id: "", server_url: "http://127.0.0.1:25555/api/ets2/telemetry", enabled: false });
  const [tab, setTab] = useState("pending");
  const [editing, setEditing] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const source = status?.source;
  useEffect(() => { if (source) setForm({ driver_id: source.driver_id || "", truck_id: source.truck_id || "", server_url: source.server_url, enabled: !!source.enabled }); }, [source?.driver_id, source?.truck_id, source?.server_url, source?.enabled]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { const id = setInterval(() => { reloadStatus(); reloadEvents(); }, 5000); return () => clearInterval(id); }, [reloadStatus, reloadEvents]);
  const save = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try { await api.put("/telemetry/settings", { ...form, driver_id: Number(form.driver_id), truck_id: Number(form.truck_id) }); toast.success("Telemetry settings saved"); reloadStatus(); }
    catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };
  const download = async (launcher = false) => {
    try { const r = await api.get(launcher ? "/telemetry/launcher" : "/telemetry/bridge", { responseType: "blob" }); downloadBlob(r.data, launcher ? "StartMcCoyTelemetry.bat" : "McCoyTelemetry.py"); }
    catch (e) { setError(errMsg(e)); }
  };
  const dismiss = async (event) => {
    if (!window.confirm(`Dismiss this detected ${event.kind}? No company record will be created.`)) return;
    try { await api.post(`/telemetry/events/${event.id}/review`, { action: "dismiss" }); reloadEvents(); toast.success("Detection dismissed"); }
    catch (e) { setError(errMsg(e)); }
  };
  const fresh = source?.last_seen && Date.now() - new Date(source.last_seen).getTime() < 15000;
  const connected = fresh && source?.live?.connected && source?.enabled;
  const label = !source?.enabled ? "Disabled" : !fresh ? "Waiting for local connection" : !source.live?.connected ? "Waiting for simulator" : source.live?.paused ? "Game paused" : "Receiving telemetry";
  const visible = (events || []).filter((e) => tab === "pending" ? e.status === "pending" : e.status !== "pending");
  return <div data-testid="telemetry-page">
    <PageHeader kicker="SCS · ETS2 / ATS" title="Live telemetry"><Button variant="outline" data-testid="telemetry-refresh" onClick={() => { reloadStatus(); reloadEvents(); }}><RefreshCw size={16} className="mr-2" />Refresh</Button></PageHeader>
    <div className="mb-8 flex flex-wrap items-center gap-3 border-y border-border py-4"><Radio className={connected ? "text-primary" : "text-muted-foreground"} /><span data-testid="telemetry-connection-status" className="font-semibold">{label}</span><span data-testid="telemetry-last-seen" className="ml-auto text-xs text-muted-foreground">{source?.last_seen ? `Last signal ${new Date(source.last_seen).toLocaleTimeString()}` : "No signals received"}</span></div>
    {(error || statusError || eventsError) && <p role="alert" data-testid="telemetry-error" className="mb-5 text-sm text-destructive">{error || errMsg(statusError || eventsError)}</p>}
    <section className="mb-10"><h2 className="mb-4 font-heading text-lg font-bold">Your game connection</h2>
      <form onSubmit={save} className="grid items-end gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[["driver_id", "Driver", drivers, "name"], ["truck_id", "Truck number", trucks, "truck_number"]].map(([key, label, options, name]) => <div key={key} className="min-w-0"><Label htmlFor={`telemetry-${key}`}>{label}</Label><select id={`telemetry-${key}`} data-testid={`telemetry-${key}`} required className="form-select mt-2" value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })}><option value="">Select {label.toLowerCase()}</option>{options.map((o) => <option key={o.id} value={o.id}>{o[name]}</option>)}</select></div>)}
        <div className="min-w-0 sm:col-span-2"><Label htmlFor="telemetry-url">Local Funbit / SCS server URL</Label><Input id="telemetry-url" data-testid="telemetry-server-url" required value={form.server_url} className="mt-2 font-mono text-xs" onChange={(e) => setForm({ ...form, server_url: e.target.value })} /></div>
        <label className="flex items-center gap-3 text-sm"><input type="checkbox" data-testid="telemetry-enabled" checked={form.enabled} onChange={(e) => setForm({ ...form, enabled: e.target.checked })} className="h-4 w-4 accent-primary" />Enable detection</label>
        <div className="flex flex-wrap gap-2 sm:col-span-1 xl:col-span-3"><Button data-testid="telemetry-save-settings" disabled={busy}>{busy ? "Saving…" : "Save connection"}</Button>{!status?.desktop && <><Button type="button" variant="outline" data-testid="telemetry-download-bridge" onClick={() => download()}><Download size={16} className="mr-2" />Download local bridge</Button><Button type="button" variant="outline" data-testid="telemetry-download-launcher" onClick={() => download(true)}><Download size={16} className="mr-2" />Windows launcher</Button></>}</div>
      </form>
      <details className="mt-5 border-l-2 border-primary pl-4 text-sm text-muted-foreground"><summary data-testid="telemetry-setup-details" className="cursor-pointer text-primary">Connection requirements</summary><div className="mt-3 space-y-2" data-testid="telemetry-setup-copy"><p>Requires the <a data-testid="telemetry-server-docs" className="text-primary underline" href="https://github.com/Funbit/ets2-telemetry-server" target="_blank" rel="noreferrer">Funbit SCS telemetry web server</a> and its game plugin running on your driving PC.</p><p>{status?.desktop ? "The desktop app samples your local server while the app is open." : "Install Python 3.10 or newer on your driving PC. Download the bridge and Windows launcher into the same folder, then double-click StartMcCoyTelemetry.bat and sign in. Keep the window open while driving. The launcher leaves errors visible. Do not expose the telemetry port to the internet."}</p><p>Fuel prices and final delivery outcomes are not supplied by this server. All detections require review. ETS2 pay is not automatically converted to USD.</p></div></details>
    </section>
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h2 className="font-heading text-lg font-bold">Detected activity</h2><div className="flex gap-2" role="tablist">{["pending", "history"].map((t) => <Button key={t} role="tab" aria-selected={tab === t} data-testid={`telemetry-tab-${t}`} variant={tab === t ? "default" : "outline"} onClick={() => setTab(t)}>{t === "pending" ? `To review (${(events || []).filter((e) => e.status === "pending").length})` : "History"}</Button>)}</div></div>
    {!events && !eventsError && <p data-testid="telemetry-loading">Loading detections…</p>}
    {events && !visible.length && <div data-testid="telemetry-empty" className="border-y border-dashed border-border py-12 text-center text-sm text-muted-foreground">{tab === "pending" ? "No loads or fuel stops awaiting review." : "No reviewed detections yet."}</div>}
    <div className="space-y-3">{visible.map((e) => <article key={e.id} data-testid={`telemetry-event-${e.id}`} className="flex flex-wrap items-center gap-4 rounded-lg border border-border bg-card p-5">{e.kind === "fuel" ? <Fuel className="shrink-0 text-primary" /> : <PackageCheck className="shrink-0 text-primary" />}<div className="min-w-0 flex-1"><div data-testid={`telemetry-event-title-${e.id}`} className="break-words font-semibold">{e.kind === "fuel" ? `${num(e.payload.gallons, 2)} US gal · Fuel increase` : `${e.payload.origin} → ${e.payload.destination}`}</div><div className="mt-1 text-xs text-muted-foreground">{e.payload.game} · {new Date(e.detected_at).toLocaleString()}</div><div data-testid={`telemetry-event-status-${e.id}`} className="mt-1 text-xs uppercase text-primary">{e.status === "pending" ? "Unconfirmed" : e.status}</div></div>{e.status === "pending" && <div className="flex flex-wrap gap-2"><Button data-testid={`telemetry-dismiss-${e.id}`} variant="ghost" onClick={() => dismiss(e)}>Dismiss</Button><Button data-testid={`telemetry-review-${e.id}`} onClick={() => setEditing(e)}>Review</Button></div>}<DeleteEntryButton table="telemetry/events" row={e} label={`Detected ${e.kind} · ${new Date(e.detected_at).toLocaleString()}`} testId={`telemetry-delete-${e.id}`} /></article>)}</div>
    {editing && <TelemetryReview key={editing.id} event={editing} drivers={drivers} trucks={trucks} onClose={() => setEditing(null)} onSaved={reloadEvents} />}
  </div>;
}