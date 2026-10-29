import { useState } from "react";
import { LogOut, LoaderCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";

export const LogoutButton = ({ testId = "header-logout-btn", sidebar = false }) => {
  const { logout } = useAuth();
  const [busy, setBusy] = useState(false);
  const signOut = async () => {
    if (busy) return;
    setBusy(true);
    try { await logout(); }
    catch { toast.error(<span data-testid={`${testId}-error`}>Could not confirm logout. Check your connection and try again.</span>, { id: "logout-failed" }); }
    finally { setBusy(false); }
  };
  return <Button type="button" data-testid={testId} variant={sidebar ? "ghost" : "outline"} disabled={busy} onClick={signOut} className={sidebar ? "w-full justify-start gap-2 text-muted-foreground hover:text-destructive" : "gap-2 border-destructive/35 text-destructive hover:bg-destructive/10 hover:text-destructive"}>
    {busy ? <LoaderCircle size={16} className="animate-spin" /> : <LogOut size={16} />}{busy ? "Signing out…" : "Log out"}
  </Button>;
};