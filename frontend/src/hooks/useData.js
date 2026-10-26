import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useDateRange } from "@/context/DateRangeContext";

export function useFetch(path, params) {
  const [data, setData] = useState(null);
  const key = JSON.stringify(params || {});
  const reload = useCallback(() => api.get(path, { params: JSON.parse(key) }).then((r) => setData(r.data)), [path, key]);
  useEffect(() => {
    reload();
  }, [reload]);
  return [data, reload];
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
