import { useState } from "react";
import { Database, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { PageHeader, Panel } from "@/components/Bits";
import { useFetch } from "@/hooks/useData";
import { api, errMsg } from "@/lib/api";

export default function TestData() {
  const [status, reload] = useFetch("/test-data");
  const [busy, setBusy] = useState(false);
  const total = status ? Object.values(status).reduce((a, b) => a + b, 0) : 0;

  const act = async (method, msg) => {
    setBusy(true);
    try {
      await api[method]("/test-data");
      toast.success(msg);
      await reload();
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="test-data-page">
      <PageHeader kicker="Sandbox" title="Test data" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Sample records">
          <p className="mb-5 text-sm leading-relaxed text-slate-400">
            Add a realistic set of sample trucks, drivers, loads, fuel, expenses and DOT inspections to explore the app.
            Removing it deletes only the sample records — anything you entered yourself is never touched.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button data-testid="seed-test-data-btn" disabled={busy} onClick={() => act("post", "Sample data added")} className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
              <Database className="mr-2 h-4 w-4" /> {total ? "Reload sample data" : "Add sample data"}
            </Button>
            <Button data-testid="clear-test-data-btn" disabled={busy || !total} onClick={() => act("delete", "Sample data removed")} variant="outline" className="border-rose-500/40 bg-transparent text-rose-400 hover:bg-rose-500/10 hover:text-rose-300">
              <Trash2 className="mr-2 h-4 w-4" /> Remove sample data
            </Button>
          </div>
        </Panel>
        <Panel title="Sample records in the database" testId="test-data-status">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {status && Object.entries(status).map(([k, v]) => (
              <div key={k} className="rounded border border-slate-800 bg-[#0B0F17] p-3">
                <div className="font-mono text-[10px] uppercase tracking-widest text-slate-500">{k}</div>
                <div className="font-mono text-xl text-cyan-400" data-testid={`test-count-${k}`}>{v}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
