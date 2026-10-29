import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useDateRange } from "@/context/DateRangeContext";

export function useFetch(path, params) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const key = JSON.stringify(params || {});
  const reqId = useRef(0);
  const reload = useCallback(() => {
    const id = ++reqId.current;
    return api.get(path, { params: JSON.parse(key) })
      .then((r) => { if (id === reqId.current) { setData(r.data); setError(null); } })
      .catch((e) => { if (id === reqId.current) setError(e); });
  }, [path, key]);
  useEffect(() => {
    setData(null); setError(null);
    reload();
    return () => { reqId.current += 1; };
  }, [reload]);
  useEffect(() => {
    window.addEventListener("company-records-changed", reload);
    return () => window.removeEventListener("company-records-changed", reload);
  }, [reload]);
  return [data, reload, error];
}

export function useRangedFetch(path) {
  const { params } = useDateRange();
  return useFetch(path, params);
}

export function useLookups() {
  const [trucks, reloadTrucks] = useFetch("/trucks");
  const [drivers, reloadDrivers] = useFetch("/drivers");
  const [categories, reloadCategories] = useFetch("/categories");
  return {
    trucks: trucks || [],
    drivers: drivers || [],
    categories: categories || [],
    reload: () => Promise.all([reloadTrucks(), reloadDrivers(), reloadCategories()]),
  };
}
