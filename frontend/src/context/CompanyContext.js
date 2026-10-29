import { createContext, useContext, useEffect, useLayoutEffect, useState } from "react";
import { api } from "@/lib/api";
import { useTheme } from "@/context/ThemeContext";
import { DEFAULT_BRANDING, brandingVariables } from "@/lib/branding";

const Context = createContext(null);
export const CompanyProvider = ({ children }) => {
  const [company, setCompany] = useState(DEFAULT_BRANDING);
  const { theme } = useTheme();
  useEffect(() => { api.get("/company/branding").then((r) => setCompany(r.data)).catch(() => {}); }, []);
  useLayoutEffect(() => {
    document.title = `${company.company_name} | Fleet Manager`;
    Object.entries(brandingVariables(company, theme)).forEach(([key, value]) => document.documentElement.style.setProperty(key, value));
  }, [company, theme]);
  return <Context.Provider value={{ company, setCompany }}>{children}</Context.Provider>;
};
export const useCompany = () => useContext(Context);