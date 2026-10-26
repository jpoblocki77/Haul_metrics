import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const NONE = "__none__";

export function lookupOptions(field, lookups) {
  if (field.options) return field.options.map((o) => (typeof o === "string" ? { value: o, label: o } : o));
  if (field.lookup === "trucks") return lookups.trucks.map((t) => ({ value: String(t.id), label: `#${t.truck_number} (${t.tank_gallons} gal)` }));
  if (field.lookup === "drivers") return lookups.drivers.map((d) => ({ value: String(d.id), label: d.name }));
  if (field.lookup === "categories") return lookups.categories.map((c) => ({ value: String(c.id), label: c.name }));
  return [];
}

export default function FieldInput({ field, value, onChange, lookups }) {
  const id = `field-${field.name}`;
  const testId = `input-${field.name.replace(/_/g, "-")}`;
  let control;
  if (field.type === "select") {
    const opts = lookupOptions(field, lookups);
    control = (
      <Select value={value == null || value === "" ? (field.required ? undefined : NONE) : String(value)} onValueChange={(v) => onChange(v === NONE ? null : v)}>
        <SelectTrigger id={id} data-testid={testId} className="border-slate-700 bg-[#0B0F17]">
          <SelectValue placeholder={`Select ${field.label.toLowerCase()}`} />
        </SelectTrigger>
        <SelectContent className="border-slate-700 bg-[#111827] text-slate-100">
          {!field.required && <SelectItem value={NONE}>— None —</SelectItem>}
          {opts.map((o) => (
            <SelectItem key={o.value} value={o.value} data-testid={`${testId}-option-${o.value}`}>{o.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  } else if (field.type === "textarea") {
    control = <Textarea id={id} data-testid={testId} value={value ?? ""} onChange={(e) => onChange(e.target.value)} className="border-slate-700 bg-[#0B0F17]" />;
  } else {
    control = (
      <Input
        id={id}
        data-testid={testId}
        type={field.type || "text"}
        step={field.step || "any"}
        value={value ?? ""}
        placeholder={field.placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="border-slate-700 bg-[#0B0F17] font-mono"
      />
    );
  }
  return (
    <div className={`space-y-1.5 ${field.full ? "sm:col-span-2" : ""}`}>
      <Label htmlFor={id} className="font-mono text-[11px] uppercase tracking-wider text-slate-400">
        {field.label}{field.required && <span className="text-amber-500"> *</span>}
      </Label>
      {control}
      {field.hint && <p className="text-[11px] text-slate-500">{field.hint}</p>}
    </div>
  );
}
