import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

// Use relative path in production (via nginx proxy). If you want a direct backend URL,
// set VITE_API_URL explicitly.
export const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";
const ACCESS_TOKEN_KEY = "access_token";

// Token storage - sync between localStorage and in-memory
let accessToken: string | null = null;

// Initialize from localStorage on module load
if (typeof window !== "undefined") {
    accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string | null) {
    accessToken = token;
    if (typeof window !== "undefined") {
        if (token) {
            localStorage.setItem(ACCESS_TOKEN_KEY, token);
        } else {
            localStorage.removeItem(ACCESS_TOKEN_KEY);
        }
    }
}

export function getAccessToken(): string | null {
    // Always check localStorage first to ensure sync
    if (typeof window !== "undefined") {
        const stored = localStorage.getItem(ACCESS_TOKEN_KEY);
        if (stored !== accessToken) {
            accessToken = stored;
        }
    }
    return accessToken;
}

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor: Add access token to requests
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = getAccessToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor: Handle token refresh on 401
api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            const refreshToken = localStorage.getItem("refresh_token");
            if (!refreshToken) {
                // No refresh token, clear tokens and redirect to login
                setAccessToken(null);
                localStorage.removeItem("refresh_token");
                if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
                    window.location.href = "/login";
                }
                return Promise.reject(error);
            }

            try {
                const response = await axios.post(`${API_BASE_URL}/users/refresh`, {
                    refresh_token: refreshToken,
                });

                const { access_token, refresh_token: newRefreshToken } = response.data;
                
                // Update token in both memory and localStorage
                setAccessToken(access_token);
                if (newRefreshToken) {
                    localStorage.setItem("refresh_token", newRefreshToken);
                }

                // Retry original request with new token
                originalRequest.headers.Authorization = `Bearer ${access_token}`;
                return api(originalRequest);
            } catch (refreshError) {
                // Refresh failed, clear tokens and redirect to login
                setAccessToken(null);
                localStorage.removeItem("refresh_token");
                if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
                    window.location.href = "/login";
                }
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default api;

