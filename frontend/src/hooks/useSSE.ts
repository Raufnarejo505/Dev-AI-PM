import { useEffect, useRef, useState } from "react";
import { getAccessToken } from "../api";

interface SSEMessage {
    type: string;
    data?: any;
    timestamp?: string;
}

export function useSSE(url: string, onMessage?: (message: SSEMessage) => void) {
    const [isConnected, setIsConnected] = useState(false);
    const eventSourceRef = useRef<EventSource | null>(null);
    const onMessageRef = useRef(onMessage);

    // Keep onMessage ref updated
    useEffect(() => {
        onMessageRef.current = onMessage;
    }, [onMessage]);

    useEffect(() => {
        const token = getAccessToken();
        if (!token) {
            console.warn("No access token available for SSE connection");
            return;
        }

        // SSE endpoint should handle auth via query param or cookie
        // Use relative path in production (via nginx proxy), or full URL in development
        const API_BASE_URL = import.meta.env.VITE_API_URL || (typeof window !== "undefined" && window.location.hostname === "localhost" ? "http://localhost:8000" : "/api");
        const sseUrl = url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
        
        // Note: EventSource doesn't support custom headers, so we need to use query param
        // The backend should support token as query parameter for SSE endpoints
        // If not, we may need to use a proxy or fetch with ReadableStream
        const urlWithToken = `${sseUrl}?token=${encodeURIComponent(token)}`;
        const eventSource = new EventSource(urlWithToken);

        eventSource.onopen = () => {
            setIsConnected(true);
        };

        eventSource.onmessage = (event) => {
            try {
                const message: SSEMessage = JSON.parse(event.data);
                if (onMessageRef.current) {
                    onMessageRef.current(message);
                }
            } catch (error) {
                console.error("Failed to parse SSE message:", error);
            }
        };

        eventSource.onerror = (error) => {
            console.error("SSE error:", error);
            setIsConnected(false);
            
            // Reconnect after delay if connection closed
            if (eventSource.readyState === EventSource.CLOSED) {
                const delay = 5000;
                const timeoutId = window.setTimeout(() => {
                    const newToken = getAccessToken();
                    if (newToken) {
                        const newUrl = `${sseUrl}?token=${encodeURIComponent(newToken)}`;
                        eventSourceRef.current = new EventSource(newUrl);
                    }
                }, delay);
                return () => clearTimeout(timeoutId);
            }
        };

        eventSourceRef.current = eventSource;

        return () => {
            eventSource.close();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [url]);

    return { isConnected };
}

