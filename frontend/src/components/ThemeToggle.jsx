import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { Button } from "@/components/ui/button";

export const ThemeToggle = ({ testId = "theme-toggle" }) => {
  const { theme, toggleTheme } = useTheme();
  const dark = theme === "dark";
  return <Button data-testid={testId} type="button" variant="outline" onClick={toggleTheme} aria-label={dark ? "Switch to light mode" : "Switch to dark mode"} title={dark ? "Switch to light mode" : "Switch to dark mode"} className="gap-2 border-border bg-background text-foreground transition-colors hover:bg-secondary">
    {dark ? <Sun size={16} /> : <Moon size={16} />}<span>{dark ? "Light mode" : "Dark mode"}</span>
  </Button>;
};