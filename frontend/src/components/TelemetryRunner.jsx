import { useEffect } from "react";
import { api } from "@/lib/api";

// Live device sampling, not a scheduled business task. Lives above page routes.
export const TelemetryRunner = () => {
  useEffect(() => {
    let stopped = false, timer;
    const tick = async () => {
      try {
        const { data } = await api.get("/telemetry/status");
        if (!data.desktop) return;
        if (data.source?.enabled && !stopped) await api.post("/telemetry/local-poll");
      } catch { /* Connection state is visible on the telemetry page. */ }
      if (!stopped) timer = setTimeout(tick, 1000);
    };
    tick();
    return () => { stopped = true; clearTimeout(timer); };
  }, []);
  return null;
};