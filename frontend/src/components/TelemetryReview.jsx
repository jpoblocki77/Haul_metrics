import { useState } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { api, errMsg, money } from "@/lib/api";

export const TelemetryReview = ({ event, drivers, trucks, onClose, onSaved }) => {
  const fuel = event.kind === "fuel";
  const [form, setForm] = useState(event.payload);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const fields = fuel ? [["date", "Purchase date", "date", true], ["gallons", "US gallons purchased", "number", true], ["price_per_gallon", "Price per US gallon (USD)", "number", true], ["miles", "Miles since last full tank", "number"], ["location", "Fuel stop", "text"]] : [["origin", "Origin", "text", true], ["destination", "Destination", "text", true], ["cargo", "Cargo", "text"], ["pay", "Actual pay (USD)", "number", true], ["miles", "Miles", "number"], ["due_date", "Due date (real calendar)", "date"], ["delivered_date", "Delivery date (real calendar)", "date", true]];
  const save = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    const record = { ...form };
    for (const key of ["gallons", "price_per_gallon", "miles", "pay", "driver_id", "truck_id"]) record[key] = record[key] === "" || record[key] == null ? null : Number(record[key]);
    for (const key of ["due_date", "delivered_date"]) if (!record[key]) record[key] = null;
    try { await api.post(`/telemetry/events/${event.id}/review`, { action: "approve", record }); toast.success(fuel ? "Fuel purchase saved" : "Load and linked income saved"); onSaved(); onClose(); }
    catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };
  return <Dialog open onOpenChange={(open) => !open && !busy && onClose()}><DialogContent data-testid="telemetry-review-dialog" className="max-h-[90vh] overflow-y-auto bg-card sm:max-w-2xl"><DialogHeader><DialogTitle>{fuel ? "Review fuel stop" : "Review detected load"}</DialogTitle><DialogDescription data-testid="telemetry-review-note">{event.payload.note}</DialogDescription></DialogHeader>
    <form onSubmit={save} className="space-y-5"><div className="grid gap-4 sm:grid-cols-2">
      {[["driver_id", "Driver", drivers, "name"], ["truck_id", "Truck number", trucks, "truck_number"]].map(([key, label, options, display]) => <div key={key}><Label htmlFor={`review-${key}`}>{label}</Label><select id={`review-${key}`} data-testid={`telemetry-review-${key}`} required className="form-select mt-2" value={form[key] || ""} onChange={(e) => set(key, e.target.value)}><option value="">Select {label.toLowerCase()}</option>{options.map((o) => <option key={o.id} value={o.id}>{o[display]}</option>)}</select></div>)}
      {fields.map(([key, label, type, required]) => <div key={key}><Label htmlFor={`review-${key}`}>{label}</Label><Input id={`review-${key}`} data-testid={`telemetry-review-${key}`} type={type} required={required} step={type === "number" ? "any" : undefined} min={type === "number" ? (key === "gallons" || key === "price_per_gallon" ? "0.0001" : "0") : undefined} className="mt-2" value={form[key] ?? ""} onChange={(e) => set(key, e.target.value)} /></div>)}
      {!fuel && <div><Label htmlFor="review-status">Confirmed delivery status</Label><select id="review-status" data-testid="telemetry-review-status" required className="form-select mt-2" value={form.status || ""} onChange={(e) => set("status", e.target.value)}><option value="">Select after delivery</option><option>On Time</option><option>Late</option></select></div>}
    </div>
    {fuel && <div data-testid="telemetry-review-total" className="border-y border-border py-3 font-mono">Purchase total: {form.price_per_gallon ? money(Number(form.gallons) * Number(form.price_per_gallon)) : "—"}</div>}
    {error && <p role="alert" data-testid="telemetry-review-error" className="text-sm text-destructive">{error}</p>}
    <div className="flex justify-end gap-2"><Button type="button" data-testid="telemetry-review-cancel" variant="outline" disabled={busy} onClick={onClose}>Cancel</Button><Button data-testid="telemetry-review-save" disabled={busy}>{busy ? "Saving…" : fuel ? "Confirm purchase" : "Confirm completed load"}</Button></div>
    </form>
  </DialogContent></Dialog>;
};