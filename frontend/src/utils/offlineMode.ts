/**
 * Offline Mode & Service Fallback System
 * Ensures UI works even when backend/services fail
 * Uses jQuery for async operations and local storage for persistence
 */

// Service health status
export interface ServiceStatus {
    backend: boolean;
    ai: boolean;
    mqtt: boolean;
    lastCheck: number;
}

// Mock data generators for offline mode
class MockDataGenerator {
    static generateMachines() {
        return [
            { id: "mock-1", name: "Pump-01", status: "online", location: "Building A", criticality: "medium" },
            { id: "mock-2", name: "Motor-02", status: "online", location: "Building B", criticality: "low" },
            { id: "mock-3", name: "Compressor-A", status: "warning", location: "Building C", criticality: "high" },
        ];
    }

    static generatePredictions() {
        const statuses = ["normal", "warning", "critical"];
        const predictions = [];
        for (let i = 0; i < 20; i++) {
            predictions.push({
                id: `mock-pred-${i}`,
                machine_id: `mock-${(i % 3) + 1}`,
                sensor_id: `mock-sensor-${i}`,
                status: statuses[Math.floor(Math.random() * statuses.length)],
                score: Math.random() * 0.5 + (i % 3 === 2 ? 0.5 : 0),
                confidence: 0.7 + Math.random() * 0.2,
                timestamp: new Date(Date.now() - i * 60000).toISOString(),
            });
        }
        return predictions;
    }

    static generateAlarms() {
        return [
            {
                id: "mock-alarm-1",
                machine_id: "mock-3",
                severity: "warning",
                message: "Temperature above threshold",
                status: "active",
                created_at: new Date().toISOString(),
            },
        ];
    }

    static generateKPIs() {
        return {
            machines: { total: 3, online: 2 },
            sensors: { total: 12 },
            alarms: { active: 1 },
            predictions: { last_24h: 20 },
        };
    }
}

// Service health checker
class ServiceHealthChecker {
    private static status: ServiceStatus = {
        backend: true,
        ai: true,
        mqtt: true,
        lastCheck: 0,
    };

    private static readonly CHECK_INTERVAL = 30000; // 30 seconds

    static async checkServices(): Promise<ServiceStatus> {
        const now = Date.now();
        if (now - this.status.lastCheck < this.CHECK_INTERVAL) {
            return this.status;
        }

        const apiBase = (window as any).VITE_API_URL || "/api";

        const token = localStorage.getItem("access_token");
        const authHeaders: any = token ? { Authorization: `Bearer ${token}` } : {};

        // Check backend
        try {
            await $.ajax({
                url: `${apiBase}/health/live`,
                method: "GET",
                timeout: 3000,
            });
            this.status.backend = true;
        } catch {
            this.status.backend = false;
        }

        // Check AI service
        try {
            await $.ajax({
                url: `${apiBase}/ai/status`,
                method: "GET",
                headers: authHeaders,
                timeout: 3000,
            });
            this.status.ai = true;
        } catch {
            this.status.ai = false;
        }

        // MQTT status (via backend)
        try {
            await $.ajax({
                url: `${apiBase}/mqtt/status`,
                method: "GET",
                headers: authHeaders,
                timeout: 3000,
            });
            this.status.mqtt = true;
        } catch {
            this.status.mqtt = false;
        }

        this.status.lastCheck = now;
        return this.status;
    }

    static getStatus(): ServiceStatus {
        return { ...this.status };
    }

    static isBackendAvailable(): boolean {
        return this.status.backend;
    }
}

// Offline data manager
class OfflineDataManager {
    private static readonly STORAGE_PREFIX = "pm_offline_";
    private static readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

    static save(key: string, data: any): void {
        try {
            const entry = {
                data,
                timestamp: Date.now(),
            };
            localStorage.setItem(this.STORAGE_PREFIX + key, JSON.stringify(entry));
        } catch (e) {
            console.warn("Failed to save offline data:", e);
        }
    }

    static load(key: string): any | null {
        try {
            const stored = localStorage.getItem(this.STORAGE_PREFIX + key);
            if (!stored) return null;

            const entry = JSON.parse(stored);
            const age = Date.now() - entry.timestamp;

            if (age > this.CACHE_TTL) {
                localStorage.removeItem(this.STORAGE_PREFIX + key);
                return null;
            }

            return entry.data;
        } catch {
            return null;
        }
    }

    static clear(key?: string): void {
        if (key) {
            localStorage.removeItem(this.STORAGE_PREFIX + key);
        } else {
            // Clear all offline data
            Object.keys(localStorage)
                .filter((k) => k.startsWith(this.STORAGE_PREFIX))
                .forEach((k) => localStorage.removeItem(k));
        }
    }

    static getMockData(type: string): any {
        switch (type) {
            case "machines":
                return MockDataGenerator.generateMachines();
            case "predictions":
                return MockDataGenerator.generatePredictions();
            case "alarms":
                return MockDataGenerator.generateAlarms();
            case "kpis":
                return MockDataGenerator.generateKPIs();
            default:
                return null;
        }
    }
}

// Main offline-aware API client
export class OfflineAwareAPI {
    private static apiBase: string = (window as any).VITE_API_URL || "/api";

    static setApiBase(url: string): void {
        this.apiBase = url;
    }

    /**
     * Make API call with offline fallback
     */
    static async request<T>(
        endpoint: string,
        options: {
            method?: string;
            data?: any;
            useCache?: boolean;
            useMock?: boolean;
            timeout?: number;
        } = {}
    ): Promise<T> {
        const {
            method = "GET",
            data,
            useCache = true,
            useMock = true,
            timeout = 10000,
        } = options;

        const cacheKey = `${method}_${endpoint}`;

        // Check service health
        const health = await ServiceHealthChecker.checkServices();
        const isOffline = !health.backend;

        // Try cache first if offline or cache enabled
        if (useCache && (isOffline || method === "GET")) {
            const cached = OfflineDataManager.load(cacheKey);
            if (cached) {
                console.log(`[OfflineAPI] Using cached data for ${endpoint}`);
                // Return cached immediately, refresh in background if online
                if (!isOffline) {
                    this.refreshInBackground(endpoint, options);
                }
                return cached as T;
            }
        }

        // If offline and no cache, use mock data
        if (isOffline && useMock) {
            const mockData = this.getMockDataForEndpoint(endpoint);
            if (mockData) {
                console.log(`[OfflineAPI] Using mock data for ${endpoint}`);
                return mockData as T;
            }
        }

        // Try API call
        try {
            const token = localStorage.getItem("access_token");
            const headers: any = {
                "Content-Type": "application/json",
            };
            if (token) {
                headers.Authorization = `Bearer ${token}`;
            }

            const response = await $.ajax({
                url: `${this.apiBase}${endpoint}`,
                method,
                data: data ? JSON.stringify(data) : undefined,
                headers,
                timeout,
            });

            // Cache successful GET responses
            if (useCache && method === "GET") {
                OfflineDataManager.save(cacheKey, response);
            }

            return response as T;
        } catch (error: any) {
            console.warn(`[OfflineAPI] API call failed for ${endpoint}:`, error);

            // If offline, try cache or mock
            if (useCache) {
                const cached = OfflineDataManager.load(cacheKey);
                if (cached) {
                    console.log(`[OfflineAPI] Using cached data after API failure for ${endpoint}`);
                    return cached as T;
                }
            }

            if (useMock) {
                const mockData = this.getMockDataForEndpoint(endpoint);
                if (mockData) {
                    console.log(`[OfflineAPI] Using mock data after API failure for ${endpoint}`);
                    return mockData as T;
                }
            }

            throw error;
        }
    }

    /**
     * Refresh data in background
     */
    private static async refreshInBackground(
        endpoint: string,
        options: any
    ): Promise<void> {
        setTimeout(async () => {
            try {
                const response = await this.request(endpoint, {
                    ...options,
                    useCache: false,
                    useMock: false,
                });
                const cacheKey = `${options.method || "GET"}_${endpoint}`;
                OfflineDataManager.save(cacheKey, response);
            } catch {
                // Silently fail background refresh
            }
        }, 0);
    }

    /**
     * Get mock data for specific endpoint
     */
    private static getMockDataForEndpoint(endpoint: string): any {
        if (endpoint.includes("/machines")) {
            return OfflineDataManager.getMockData("machines");
        }
        if (endpoint.includes("/predictions")) {
            return OfflineDataManager.getMockData("predictions");
        }
        if (endpoint.includes("/alarms")) {
            return OfflineDataManager.getMockData("alarms");
        }
        if (endpoint.includes("/dashboard/overview")) {
            return OfflineDataManager.getMockData("kpis");
        }
        return null;
    }

    /**
     * Batch requests with offline support
     */
    static async batch<T extends Record<string, any>>(
        requests: Record<string, { endpoint: string; options?: any }>
    ): Promise<T> {
        const results: any = {};
        const promises: Promise<any>[] = [];

        for (const [key, { endpoint, options }] of Object.entries(requests)) {
            promises.push(
                this.request(endpoint, options)
                    .then((data) => {
                        results[key] = data;
                    })
                    .catch((error) => {
                        console.warn(`[OfflineAPI] Batch request failed for ${key}:`, error);
                        results[key] = null;
                    })
            );
        }

        await Promise.all(promises);
        return results as T;
    }
}

// Export utilities
export { ServiceHealthChecker, OfflineDataManager, MockDataGenerator };

