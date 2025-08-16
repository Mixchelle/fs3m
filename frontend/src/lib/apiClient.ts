import axios from "axios";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

const isBrowser = typeof window !== "undefined";

const TOKEN_KEYS = {
  access: "access_token",
  refresh: "refresh_token",
};

export function getAccessToken() {
  if (!isBrowser) return null;
  return localStorage.getItem(TOKEN_KEYS.access);
}
export function getRefreshToken() {
  if (!isBrowser) return null;
  return localStorage.getItem(TOKEN_KEYS.refresh);
}
export function setTokens(access: string, refresh: string) {
  if (!isBrowser) return;
  localStorage.setItem(TOKEN_KEYS.access, access);
  localStorage.setItem(TOKEN_KEYS.refresh, refresh);
}
export function clearTokens() {
  if (!isBrowser) return;
  localStorage.removeItem(TOKEN_KEYS.access);
  localStorage.removeItem(TOKEN_KEYS.refresh);
}

export const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: false,
});

// Injeta Authorization
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers || {};
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh automático em 401
let refreshing = false;
let pendingRequests: Array<(token: string | null) => void> = [];

function onRrefreshed(token: string | null) {
  pendingRequests.forEach((cb) => cb(token));
  pendingRequests = [];
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const status = error?.response?.status;

    if (status === 401 && !original._retry) {
      original._retry = true;

      if (refreshing) {
        // fila enquanto atualiza
        return new Promise((resolve, reject) => {
          pendingRequests.push((newToken) => {
            if (!newToken) reject(error);
            else {
              original.headers.Authorization = `Bearer ${newToken}`;
              resolve(api(original));
            }
          });
        });
      }

      refreshing = true;
      try {
        const refresh = getRefreshToken();
        if (!refresh) throw new Error("No refresh token");

        const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, {
          refresh,
        });
        const newAccess = data?.access;
        if (!newAccess) throw new Error("No access in refresh");

        setTokens(newAccess, refresh);
        onRrefreshed(newAccess);
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      } catch (e) {
        clearTokens();
        onRrefreshed(null);
        return Promise.reject(e);
      } finally {
        refreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
