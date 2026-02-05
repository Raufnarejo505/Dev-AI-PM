/**
 * Async Operations Utility (Enhanced)
 * Provides jQuery-based async operations so UI doesn't fully depend on backend
 * Enables offline functionality, local caching, and smooth UX
 * 
 * NOTE: This is the legacy version. For new code, use offlineMode.ts instead.
 */

// Local storage cache for offline support
const CACHE_PREFIX = "pm_cache_";
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

interface CacheEntry {
    data: any;
    timestamp: number;
    ttl: number;
}

/**
 * Get cached data if available and not expired
 */
export function getCached(key: string): any | null {
    try {
        const cached = localStorage.getItem(CACHE_PREFIX + key);
        if (!cached) return null;
        
        const entry: CacheEntry = JSON.parse(cached);
        const now = Date.now();
        
        if (now - entry.timestamp > entry.ttl) {
            localStorage.removeItem(CACHE_PREFIX + key);
            return null;
        }
        
        return entry.data;
    } catch {
        return null;
    }
}

/**
 * Set cached data with TTL
 */
export function setCached(key: string, data: any, ttl: number = CACHE_TTL): void {
    try {
        const entry: CacheEntry = {
            data,
            timestamp: Date.now(),
            ttl,
        };
        localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(entry));
    } catch (e) {
        console.warn("Failed to cache data:", e);
    }
}

/**
 * Async API call with jQuery, caching, and offline support
 */
export async function asyncApiCall(
    url: string,
    options: {
        method?: string;
        data?: any;
        cache?: boolean;
        cacheKey?: string;
        timeout?: number;
    } = {}
): Promise<any> {
    const {
        method = "GET",
        data,
        cache = true,
        cacheKey = url,
        timeout = 10000,
    } = options;

    // Check cache first
    if (cache && method === "GET") {
        const cached = getCached(cacheKey);
        if (cached) {
            // Return cached data immediately, then refresh in background
            setTimeout(() => {
                refreshCache(url, cacheKey, timeout);
            }, 0);
            return cached;
        }
    }

    // Make API call with jQuery
    return new Promise((resolve, reject) => {
        const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const fullUrl = url.startsWith("http") ? url : `${apiBase}${url}`;

        // Get token from localStorage
        const token = localStorage.getItem("access_token");
        const headers: any = {
            "Content-Type": "application/json",
        };
        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }

        $.ajax({
            url: fullUrl,
            method,
            data: data ? JSON.stringify(data) : undefined,
            headers,
            timeout,
            success: (response) => {
                // Cache successful GET responses
                if (cache && method === "GET") {
                    setCached(cacheKey, response);
                }
                resolve(response);
            },
            error: (xhr, status, error) => {
                // If offline, try to return cached data
                if (status === "timeout" || status === "error") {
                    const cached = getCached(cacheKey);
                    if (cached) {
                        console.warn("Using cached data due to network error");
                        resolve(cached);
                        return;
                    }
                }
                reject({ status, error, xhr });
            },
        });
    });
}

/**
 * Refresh cache in background
 */
function refreshCache(url: string, cacheKey: string, timeout: number): void {
    asyncApiCall(url, { cache: true, cacheKey, timeout }).catch(() => {
        // Silently fail - we already have cached data
    });
}

/**
 * Batch async operations for parallel execution
 */
export async function batchAsyncOperations<T>(
    operations: Array<() => Promise<T>>
): Promise<T[]> {
    return Promise.all(operations.map((op) => op()));
}

/**
 * Debounced async operation
 */
export function debounceAsync<T>(
    fn: () => Promise<T>,
    delay: number = 300
): () => Promise<T> {
    let timeoutId: ReturnType<typeof setTimeout>;
    let lastPromise: Promise<T> | null = null;

    return () => {
        return new Promise((resolve, reject) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(async () => {
                try {
                    const result = await fn();
                    resolve(result);
                } catch (error) {
                    reject(error);
                }
            }, delay);
        });
    };
}

/**
 * Retry async operation with exponential backoff
 */
export async function retryAsync<T>(
    fn: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
): Promise<T> {
    let lastError: any;
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;
            if (i < maxRetries - 1) {
                await new Promise((resolve) => setTimeout(resolve, delay * Math.pow(2, i)));
            }
        }
    }
    throw lastError;
}

