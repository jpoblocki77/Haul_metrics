import axios from "axios";

export const api = axios.create({ baseURL: `${process.env.REACT_APP_BACKEND_URL}/api`, withCredentials: true });

let csrfToken = null;
let csrfRequest = null;
export const setCsrfToken = (value) => { csrfToken = value || null; };
const fetchCsrf = async () => {
  if (!csrfRequest) {
    csrfRequest = axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/auth/csrf`, { withCredentials: true, timeout: 10000 })
      .then(({ data }) => { csrfToken = data.csrf_token; return csrfToken; })
      .finally(() => { csrfRequest = null; });
  }
  return csrfRequest;
};

api.interceptors.request.use(async (cfg) => {
  if (["post", "put", "patch", "delete"].includes(cfg.method?.toLowerCase()) && cfg.url !== "/auth/login") {
    cfg.headers["X-CSRF-Token"] = csrfToken || await fetchCsrf();
  }
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  async (err) => {
    if (err.response?.status === 403 && err.response.data?.code === "csrf_failed" && !err.config._csrfRetried) {
      err.config._csrfRetried = true;
      csrfToken = null;
      try { await fetchCsrf(); return api.request(err.config); } catch (refreshError) { return Promise.reject(refreshError); }
    }
    if (err.response?.status === 401 && !err.config.url.includes("/auth/")) {
      csrfToken = null;
      localStorage.removeItem("vtc_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export function errMsg(e) {
  const d = e?.response?.data?.detail;
  if (!d) return e?.message || "Something went wrong";
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => `${x.loc?.slice(-1)[0] ?? ""}: ${x.msg}`).join(" ");
  return String(d);
}

export const money = (v) =>
  v == null ? "—" : Number(v).toLocaleString("en-US", { style: "currency", currency: "USD" });
export const num = (v, d = 1) => (v == null || isNaN(v) ? "—" : Number(v).toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: d }));
export const pct = (v) => (v == null ? "—" : `${Number(v).toFixed(1)}%`);
export const today = () => new Date().toISOString().slice(0, 10);
