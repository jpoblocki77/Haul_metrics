import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { DeleteEntryButton } from "@/components/DeleteEntryButton";
import { useAuth } from "@/context/AuthContext";
import { useFetch } from "@/hooks/useData";
import { errMsg, money } from "@/lib/api";

const TABLES = { income: "Income", expenses: "Expenses", fuel: "Fuel purchases", loads: "Loads", inspections: "DOT inspections", drivers: "Drivers", trucks: "Trucks", categories: "Expense categories", "telemetry/events": "Telemetry detections", users: "User accounts" };
const entryLabel = (row, table) => table === "loads" ? `${row.origin} → ${row.destination}` : table === "telemetry/events" ? `${row.kind === "fuel" ? "Fuel stop" : `${row.payload.origin} → ${row.payload.destination}`} · ${row.status}` : row.name || row.username || row.source || row.description || row.location || row.result || (row.truck_number ? `Truck #${row.truck_number}` : TABLES[table]);

const EntryList = ({ table }) => {
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const paginated = table === "telemetry/events";
  const [data, reload, error] = useFetch(paginated ? "/telemetry/manage-events" : `/${table}`, paginated ? { q: query, offset, limit: 100 } : undefined);
  const rows = paginated ? data?.items : data;
  const { user } = useAuth();
  const filtered = paginated ? (rows || []) : (rows || []).filter((r) => JSON.stringify(r).toLowerCase().includes(query.toLowerCase()));
  const total = paginated ? data?.total || 0 : filtered.length;
  useEffect(() => { if (paginated && data && offset > 0 && offset >= data.total) setOffset(Math.max(0, Math.floor((data.total - 1) / 100) * 100)); }, [paginated, data, offset]);
  return <div className="min-w-0 space-y-4"><Input data-testid="delete-entries-search" aria-label="Search entries" placeholder="Search entries…" maxLength={200} value={query} onChange={(e) => { setQuery(e.target.value); setOffset(0); }} />
    <p data-testid="delete-entries-count" className="text-xs text-muted-foreground">{total} entries · all dates{paginated && total > 0 ? ` · showing ${offset + 1}–${offset + filtered.length}` : total > 100 ? " · showing first 100; search to narrow results" : ""}</p>
    {error && <p role="alert" data-testid="delete-entries-error" className="text-sm text-destructive">{errMsg(error)} <Button data-testid="delete-entries-retry" onClick={reload}>Retry</Button></p>}
    {!rows && !error && <p data-testid="delete-entries-loading">Loading entries…</p>}
    {rows && !filtered.length && <p data-testid="delete-entries-empty" className="py-6 text-center text-muted-foreground">No matching entries.</p>}
    <div className="max-h-[45vh] overflow-y-auto">{filtered.slice(0, 100).map((row) => <div data-testid={`manage-entry-${table.replaceAll("/", "-")}-${row.id}`} key={row.id} className="flex min-w-0 items-center gap-3 border-b border-border py-3"><div className="min-w-0 flex-1"><div className="break-words text-sm" style={{ overflowWrap: "anywhere" }}>{entryLabel(row, table)}</div><div className="mt-1 text-xs text-muted-foreground">{row.date || row.delivered_date || row.due_date || row.detected_at?.slice(0, 10) || row.created_at?.slice(0, 10)}{row.amount != null || row.total != null || row.pay != null ? ` · ${money(row.amount ?? row.total ?? row.pay)}` : ""} · #{row.id}</div></div>{table === "users" && row.id === user.id ? <span className="text-xs text-muted-foreground">Your account</span> : <DeleteEntryButton table={table} row={row} label={entryLabel(row, table)} testId={`manage-delete-${table.replaceAll("/", "-")}-${row.id}`} />}</div>)}</div>
    {paginated && (total > 100 || offset > 0) && <div className="flex justify-between gap-2"><Button data-testid="delete-entries-prev-page" variant="outline" disabled={!data || offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>Previous</Button><Button data-testid="delete-entries-next-page" variant="outline" disabled={!data || offset + 100 >= total} onClick={() => setOffset(offset + 100)}>Next</Button></div>}
  </div>;
};

export const ManageEntries = () => {
  const { isOwner } = useAuth();
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  const [table, setTable] = useState("income");
  if (!isOwner) return null;
  const show = () => { const current = pathname.split("/")[1]; setTable(TABLES[current] ? current : current === "telemetry" ? "telemetry/events" : "income"); setOpen(true); };
  return <div className="no-print mb-4 flex justify-end"><Button variant="outline" data-testid="open-delete-entries" onClick={show}><Trash2 size={16} className="mr-2" />Delete entries</Button>
    <Dialog open={open} onOpenChange={setOpen}><DialogContent data-testid="delete-entries-dialog" className="max-h-[90vh] overflow-y-auto bg-card sm:max-w-2xl"><DialogHeader><DialogTitle>Delete entries</DialogTitle><DialogDescription>Choose a record type. Each deletion needs a separate confirmation.</DialogDescription></DialogHeader>
      <div><Label htmlFor="delete-entry-type">Record type</Label><select id="delete-entry-type" data-testid="delete-entries-type" className="form-select mt-2" value={table} onChange={(e) => setTable(e.target.value)}>{Object.entries(TABLES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></div>
      {open && <EntryList key={table} table={table} />}
    </DialogContent></Dialog>
  </div>;
};