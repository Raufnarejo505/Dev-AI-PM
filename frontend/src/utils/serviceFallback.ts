/**
 * Service Fallback System
 * Automatically switches to offline/mock mode when services fail
 */

import { ServiceHealthChecker, OfflineDataManager } from "./offlineMode";

export class ServiceFallback {
    private static retryAttempts = 0;
    private static readonly MAX_RETRIES = 3;
    private static readonly RETRY_DELAY = 2000; // 2 seconds

    /**
     * Execute function with automatic fallback
     */
    static async execute<T>(
        apiCall: () => Promise<T>,
        fallback: () => T | Promise<T>,
        options: {
            retry?: boolean;
            useCache?: boolean;
            cacheKey?: string;
        } = {}
    ): Promise<T> {
        const { retry = true, useCache = true, cacheKey } = options;

        try {
            // Check service health first
            const health = await ServiceHealthChecker.checkServices();
            if (!health.backend && useCache && cacheKey) {
                const cached = OfflineDataManager.load(cacheKey);
                if (cached) {
                    console.log(`[ServiceFallback] Using cached data for ${cacheKey}`);
                    return cached as T;
                }
            }

            // Try API call
            const result = await this.retryIfNeeded(apiCall, retry);
            
            // Cache successful result
            if (useCache && cacheKey) {
                OfflineDataManager.save(cacheKey, result);
            }

            this.retryAttempts = 0; // Reset on success
            return result;
        } catch (error) {
            console.warn("[ServiceFallback] API call failed, using fallback:", error);
            
            // Try cache before fallback
            if (useCache && cacheKey) {
                const cached = OfflineDataManager.load(cacheKey);
                if (cached) {
                    console.log(`[ServiceFallback] Using cached data after error for ${cacheKey}`);
                    return cached as T;
                }
            }

            // Use fallback
            return await fallback();
        }
    }

    /**
     * Retry API call with exponential backoff
     */
    private static async retryIfNeeded<T>(
        apiCall: () => Promise<T>,
        retry: boolean
    ): Promise<T> {
        if (!retry) {
            return apiCall();
        }

        for (let attempt = 0; attempt < this.MAX_RETRIES; attempt++) {
            try {
                return await apiCall();
            } catch (error) {
                if (attempt === this.MAX_RETRIES - 1) {
                    throw error;
                }
                // Exponential backoff
                await new Promise((resolve) =>
                    setTimeout(resolve, this.RETRY_DELAY * Math.pow(2, attempt))
                );
            }
        }

        throw new Error("Max retries exceeded");
    }

    /**
     * Check if services are available
     */
    static async isOnline(): Promise<boolean> {
        const health = await ServiceHealthChecker.checkServices();
        return health.backend;
    }

    /**
     * Get service status
     */
    static async getServiceStatus() {
        return await ServiceHealthChecker.checkServices();
    }
}

