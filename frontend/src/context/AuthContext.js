import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.get("/auth/me").then((r) => setUser(r.data)).catch(() => setUser(false));
  }, []);

  const login = async (username, password) => {
    const { data } = await api.post("/auth/login", { username, password });
    localStorage.setItem("vtc_token", data.token);
    setUser(data.user);
  };

  const logout = async () => {
    await api.post("/auth/logout").catch(() => {});
    localStorage.removeItem("vtc_token");
    setUser(false);
  };

  return <AuthCtx.Provider value={{ user, login, logout, isOwner: user?.role === "owner" }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
