import { createContext, useContext, useLayoutEffect, useState } from "react";

const ThemeContext = createContext(null);
export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => localStorage.getItem("mccoy-theme") === "light" ? "light" : "dark");
  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.style.colorScheme = theme;
    localStorage.setItem("mccoy-theme", theme);
  }, [theme]);
  return <ThemeContext.Provider value={{ theme, toggleTheme: () => setTheme((t) => t === "dark" ? "light" : "dark") }}>{children}</ThemeContext.Provider>;
};
export const useTheme = () => useContext(ThemeContext);