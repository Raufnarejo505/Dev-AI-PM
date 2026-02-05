import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api, { setAccessToken } from "../api";

interface User {
    id: string;
    email: string;
    full_name?: string;
    role: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshToken: () => Promise<boolean>;
    isAuthenticated: boolean;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Secure token storage - sync with api/index.ts
import { setAccessToken as setApiAccessToken, getAccessToken as getApiAccessToken } from "../api";

const REFRESH_TOKEN_KEY = "refresh_token";

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Initialize auth state - Check for existing token
    useEffect(() => {
        const initAuth = async () => {
            const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
            if (refreshToken) {
                try {
                    const refreshed = await refreshTokenSilently(refreshToken);
                    if (refreshed) {
                        setIsLoading(false);
                        return;
                    }
                } catch (error) {
                    console.error("Token refresh failed:", error);
                    localStorage.removeItem(REFRESH_TOKEN_KEY);
                }
            }
            setIsLoading(false);
        };
        initAuth();
    }, []);

    const refreshTokenSilently = async (refreshToken: string): Promise<boolean> => {
        try {
            const response = await api.post("/users/refresh", { refresh_token: refreshToken }, {
                timeout: 3000, // 3 second timeout
            });
            const { access_token, refresh_token: newRefreshToken } = response.data;
            
            setToken(access_token);
            setApiAccessToken(access_token); // Update API client token (syncs with localStorage)
            
            if (newRefreshToken) {
                localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken);
            }
            
            // Fetch user profile
            await fetchUserProfile(access_token);
            return true;
        } catch (error) {
            console.error("Token refresh failed:", error);
            return false;
        }
    };

    const fetchUserProfile = async (token: string) => {
        try {
            const response = await api.get("/users/me", {
                headers: { Authorization: `Bearer ${token}` },
                timeout: 5000, // 5 second timeout
            });
            setUser(response.data);
        } catch (error) {
            console.error("Failed to fetch user profile:", error);
            // Set minimal user info from token if available
            // This prevents blocking login if profile fetch fails
        }
    };

    const login = async (email: string, password: string) => {
        // Ultra-fast login - 3 second timeout, immediate response
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
        
        try {
            const params = new URLSearchParams();
            params.append("username", email);
            params.append("password", password);

            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/users/login`, {
                method: 'POST',
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: params.toString(),
                signal: controller.signal,
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                let errorData;
                try {
                    const errorText = await response.text();
                    try {
                        errorData = JSON.parse(errorText);
                    } catch {
                        errorData = { detail: errorText || `Server error (${response.status})` };
                    }
                } catch {
                    errorData = { detail: `Server error (${response.status})` };
                }
                throw new Error(errorData.detail || 'Login failed');
            }

            const data = await response.json();
            const { access_token, refresh_token } = data;
            
            // Set tokens immediately
            setToken(access_token);
            setApiAccessToken(access_token);
            
            if (refresh_token) {
                localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);
            }

            // Set minimal user info immediately (don't wait for profile)
            setUser({
                id: 'temp',
                email: email,
                role: 'admin', // Default, will be updated by profile fetch
            });

            // Fetch full profile in background (non-blocking)
            setTimeout(() => {
                fetchUserProfile(access_token).catch(() => {
                    // Ignore errors - user is already logged in
                });
            }, 100);
        } catch (err: any) {
            clearTimeout(timeoutId);
            if (err.name === 'AbortError') {
                throw new Error('Login timeout. Please check your connection.');
            }
            throw err;
        }
    };

    const logout = async () => {
        // INSTANT LOGOUT - Clear everything immediately, don't wait for server
        setToken(null);
        setUser(null);
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        setApiAccessToken(null);
        
        // Force immediate redirect - don't wait for server response
        window.location.href = "/login";
        
        // Revoke token server-side in background (non-blocking)
        if (refreshToken) {
            api.post("/users/logout", { refresh_token: refreshToken }).catch(() => {
                // Ignore errors - logout already happened
            });
        }
    };

    const refreshToken = async (): Promise<boolean> => {
        const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
        if (!refreshToken) {
            return false;
        }
        return await refreshTokenSilently(refreshToken);
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                login,
                logout,
                refreshToken,
                isAuthenticated: !!token,
                isLoading,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

// Note: Token management is now handled by api/index.ts to ensure consistency

