import { createContext, useContext, useMemo, useState } from "react";

const Ctx = createContext(null);
const iso = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);

export function presetRange(preset) {
  const now = new Date();
  if (preset === "today") return { start: iso(now), end: iso(now) };
  if (preset === "week") {
    const s = new Date(now);
    s.setDate(now.getDate() - ((now.getDay() + 6) % 7));
    const e = new Date(s);
    e.setDate(s.getDate() + 6);
    return { start: iso(s), end: iso(e) };
  }
  if (preset === "month") return { start: iso(new Date(now.getFullYear(), now.getMonth(), 1)), end: iso(new Date(now.getFullYear(), now.getMonth() + 1, 0)) };
  if (preset === "last-month") return { start: iso(new Date(now.getFullYear(), now.getMonth() - 1, 1)), end: iso(new Date(now.getFullYear(), now.getMonth(), 0)) };
  return { start: "", end: "" };
}

export function monthRange(ym) {
  const [y, m] = ym.split("-").map(Number);
  return { start: `${ym}-01`, end: iso(new Date(y, m, 0)) };
}

export function DateRangeProvider({ children }) {
  const [preset, setPresetState] = useState("all");
  const [range, setRange] = useState({ start: "", end: "" });
  const value = useMemo(() => {
    const params = {};
    if (range.start) params.start = range.start;
    if (range.end) params.end = range.end;
    return {
      preset, ...range, params,
      setPreset: (p) => {
        setPresetState(p);
        if (p !== "custom") setRange(presetRange(p));
      },
      setCustom: (r) => {
        setPresetState("custom");
        setRange((prev) => ({ ...prev, ...r }));
      },
      inRange: (d) => !d || ((!range.start || d >= range.start) && (!range.end || d <= range.end)),
    };
  }, [preset, range]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useDateRange = () => useContext(Ctx);
