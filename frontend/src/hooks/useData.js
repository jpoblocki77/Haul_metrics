import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";

export function useFetch(path) {
  const [data, setData] = useState(null);
  const reload = useCallback(() => api.get(path).then((r) => setData(r.data)), [path]);
  useEffect(() => {
    reload();
  }, [reload]);
  return [data, reload];
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
