/**
 * React hook for offline-aware data fetching
 * Uses jQuery and offline mode system
 */
import { useState, useEffect, useCallback } from "react";
import { OfflineAwareAPI, ServiceHealthChecker } from "../utils/offlineMode";

interface UseOfflineDataOptions {
    endpoint: string;
    method?: string;
    refreshInterval?: number;
    useCache?: boolean;
    useMock?: boolean;
    dependencies?: any[];
}

export function useOfflineData<T = any>(options: UseOfflineDataOptions) {
    const {
        endpoint,
        method = "GET",
        refreshInterval = 60000, // 1 minute
        useCache = true,
        useMock = true,
        dependencies = [],
    } = options;

    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<any>(null);
    const [isOffline, setIsOffline] = useState(false);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            // Check service health
            const health = await ServiceHealthChecker.checkServices();
            setIsOffline(!health.backend);

            // Fetch data with offline support
            const result = await OfflineAwareAPI.request<T>(endpoint, {
                method,
                useCache,
                useMock,
            });

            setData(result);
        } catch (err) {
            console.error(`[useOfflineData] Error fetching ${endpoint}:`, err);
            setError(err);
        } finally {
            setLoading(false);
        }
    }, [endpoint, method, useCache, useMock, ...dependencies]);

    useEffect(() => {
        fetchData();

        if (refreshInterval > 0) {
            const interval = setInterval(fetchData, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [fetchData, refreshInterval]);

    return { data, loading, error, isOffline, refetch: fetchData };
}

