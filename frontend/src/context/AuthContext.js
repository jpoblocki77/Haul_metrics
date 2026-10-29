import { createContext, useContext, useEffect, useRef, useState } from "react";
import { api, setCsrfToken } from "@/lib/api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const authVersion = useRef(0);

  useEffect(() => {
    localStorage.removeItem("vtc_token");
    const version = authVersion.current;
    api.get("/auth/me").then((r) => { if (authVersion.current === version) setUser(r.data); }).catch(() => { if (authVersion.current === version) setUser(false); });
    const syncLogout = (event) => {
      if (event.key === "vtc_logout_event") { authVersion.current += 1; setCsrfToken(null); setUser(false); }
    };
    window.addEventListener("storage", syncLogout);
    return () => window.removeEventListener("storage", syncLogout);
  }, []);

  const login = async (username, password) => {
    const version = ++authVersion.current;
    const { data } = await api.post("/auth/login", { username, password });
    if (version !== authVersion.current) return;
    setCsrfToken(data.csrf_token);
    localStorage.removeItem("vtc_token");
    setUser(data.user);
  };

  const logout = async () => {
    try { await api.post("/auth/logout", {}, { timeout: 10000 }); }
    catch (error) { if (error.response?.status !== 401) throw error; }
    authVersion.current += 1;
    setCsrfToken(null);
    localStorage.removeItem("vtc_token");
    localStorage.setItem("vtc_logout_event", `${Date.now()}-${Math.random()}`);
    setUser(false);
  };

  return <AuthCtx.Provider value={{ user, login, logout, isOwner: user?.role === "owner" }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
