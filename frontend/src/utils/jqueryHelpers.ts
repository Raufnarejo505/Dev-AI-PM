/**
 * jQuery Helper Functions
 * Provides convenient jQuery-based utilities for async operations
 */

// Declare jQuery types
declare const $: any;

/**
 * jQuery-based API client with offline support
 */
export class jQueryAPI {
    private static baseURL: string = (window as any).VITE_API_URL || "http://localhost:8000";

    static setBaseURL(url: string): void {
        this.baseURL = url;
    }

    /**
     * GET request with jQuery
     */
    static async get<T = any>(endpoint: string, options: {
        cache?: boolean;
        timeout?: number;
        useMock?: boolean;
    } = {}): Promise<T> {
        const { cache = true, timeout = 10000, useMock = true } = options;

        return new Promise((resolve, reject) => {
            const token = localStorage.getItem("access_token");
            const headers: any = {
                "Content-Type": "application/json",
            };
            if (token) {
                headers.Authorization = `Bearer ${token}`;
            }

            $.ajax({
                url: `${this.baseURL}${endpoint}`,
                method: "GET",
                headers,
                timeout,
                cache: cache,
                success: (data: T) => {
                    // Cache response
                    if (cache) {
                        try {
                            localStorage.setItem(
                                `jquery_cache_${endpoint}`,
                                JSON.stringify({ data, timestamp: Date.now() })
                            );
                        } catch (e) {
                            console.warn("Failed to cache response:", e);
                        }
                    }
                    resolve(data);
                },
                error: (xhr: any, status: string, error: string) => {
                    // Try cache on error
                    if (cache) {
                        try {
                            const cached = localStorage.getItem(`jquery_cache_${endpoint}`);
                            if (cached) {
                                const parsed = JSON.parse(cached);
                                // Use cache if less than 5 minutes old
                                if (Date.now() - parsed.timestamp < 5 * 60 * 1000) {
                                    console.log(`[jQueryAPI] Using cached data for ${endpoint}`);
                                    resolve(parsed.data);
                                    return;
                                }
                            }
                        } catch (e) {
                            // Cache read failed
                        }
                    }

                    // Use mock data if enabled
                    if (useMock) {
                        const mockData = this.getMockData(endpoint);
                        if (mockData) {
                            console.log(`[jQueryAPI] Using mock data for ${endpoint}`);
                            resolve(mockData as T);
                            return;
                        }
                    }

                    reject({ xhr, status, error });
                },
            });
        });
    }

    /**
     * POST request with jQuery
     */
    static async post<T = any>(endpoint: string, data: any, options: {
        timeout?: number;
    } = {}): Promise<T> {
        const { timeout = 10000 } = options;

        return new Promise((resolve, reject) => {
            const token = localStorage.getItem("access_token");
            const headers: any = {
                "Content-Type": "application/json",
            };
            if (token) {
                headers.Authorization = `Bearer ${token}`;
            }

            $.ajax({
                url: `${this.baseURL}${endpoint}`,
                method: "POST",
                data: JSON.stringify(data),
                headers,
                timeout,
                success: (response: T) => {
                    resolve(response);
                },
                error: (xhr: any, status: string, error: string) => {
                    reject({ xhr, status, error });
                },
            });
        });
    }

    /**
     * PUT request with jQuery
     */
    static async put<T = any>(endpoint: string, data: any, options: {
        timeout?: number;
    } = {}): Promise<T> {
        const { timeout = 10000 } = options;

        return new Promise((resolve, reject) => {
            const token = localStorage.getItem("access_token");
            const headers: any = {
                "Content-Type": "application/json",
            };
            if (token) {
                headers.Authorization = `Bearer ${token}`;
            }

            $.ajax({
                url: `${this.baseURL}${endpoint}`,
                method: "PUT",
                data: JSON.stringify(data),
                headers,
                timeout,
                success: (response: T) => {
                    resolve(response);
                },
                error: (xhr: any, status: string, error: string) => {
                    reject({ xhr, status, error });
                },
            });
        });
    }

    /**
     * DELETE request with jQuery
     */
    static async delete<T = any>(endpoint: string, options: {
        timeout?: number;
    } = {}): Promise<T> {
        const { timeout = 10000 } = options;

        return new Promise((resolve, reject) => {
            const token = localStorage.getItem("access_token");
            const headers: any = {
                "Content-Type": "application/json",
            };
            if (token) {
                headers.Authorization = `Bearer ${token}`;
            }

            $.ajax({
                url: `${this.baseURL}${endpoint}`,
                method: "DELETE",
                headers,
                timeout,
                success: (response: T) => {
                    resolve(response);
                },
                error: (xhr: any, status: string, error: string) => {
                    reject({ xhr, status, error });
                },
            });
        });
    }

    /**
     * Get mock data for endpoint
     */
    private static getMockData(endpoint: string): any {
        if (endpoint.includes("/machines")) {
            return [
                { id: "mock-1", name: "Pump-01", status: "online", location: "Building A" },
                { id: "mock-2", name: "Motor-02", status: "online", location: "Building B" },
            ];
        }
        if (endpoint.includes("/predictions")) {
            return [
                {
                    id: "mock-pred-1",
                    status: "normal",
                    score: 0.3,
                    timestamp: new Date().toISOString(),
                },
            ];
        }
        if (endpoint.includes("/dashboard/overview")) {
            return {
                machines: { total: 2, online: 2 },
                sensors: { total: 8 },
                alarms: { active: 0 },
                predictions: { last_24h: 10 },
            };
        }
        return null;
    }

    /**
     * Batch requests
     */
    static async batch<T extends Record<string, any>>(
        requests: Record<string, { endpoint: string; method?: string; data?: any }>
    ): Promise<T> {
        const results: any = {};
        const promises: Promise<any>[] = [];

        for (const [key, config] of Object.entries(requests)) {
            const { endpoint, method = "GET", data } = config;
            promises.push(
                (method === "GET"
                    ? this.get(endpoint)
                    : method === "POST"
                    ? this.post(endpoint, data)
                    : method === "PUT"
                    ? this.put(endpoint, data)
                    : this.delete(endpoint)
                )
                    .then((data) => {
                        results[key] = data;
                    })
                    .catch((error) => {
                        console.warn(`[jQueryAPI] Batch request failed for ${key}:`, error);
                        results[key] = null;
                    })
            );
        }

        await Promise.all(promises);
        return results as T;
    }
}

