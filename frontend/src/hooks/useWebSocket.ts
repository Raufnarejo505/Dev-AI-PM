import { useEffect, useRef, useState } from "react";
import { getAccessToken } from "../api";

interface WebSocketMessage {
    type: string;
    data: any;
    timestamp?: string;
}

export function useWebSocket(url: string, onMessage?: (message: WebSocketMessage) => void) {
    const [isConnected, setIsConnected] = useState(false);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<number | null>(null);
    const heartbeatIntervalRef = useRef<number | null>(null);

    const connect = () => {
        try {
            const token = getAccessToken();
            const wsUrl = url.replace("http://", "ws://").replace("https://", "wss://");
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                setIsConnected(true);
                setReconnectAttempts(0);
                
                // Send auth token if available
                if (token) {
                    ws.send(JSON.stringify({ type: "auth", token }));
                }

                // Start heartbeat
                heartbeatIntervalRef.current = window.setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: "ping" }));
                    }
                }, 30000) as unknown as number;
            };

            ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data);
                    
                    // Handle pong
                    if (message.type === "pong") {
                        return;
                    }

                    if (onMessage) {
                        onMessage(message);
                    }
                } catch (error) {
                    console.error("Failed to parse WebSocket message:", error);
                }
            };

            ws.onerror = (error) => {
                console.error("WebSocket error:", error);
            };

            ws.onclose = () => {
                setIsConnected(false);
                
                // Clear heartbeat
                if (heartbeatIntervalRef.current) {
                    clearInterval(heartbeatIntervalRef.current);
                }

                // Exponential backoff reconnect
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                reconnectTimeoutRef.current = window.setTimeout(() => {
                    setReconnectAttempts((prev) => prev + 1);
                    connect();
                }, delay) as unknown as number;
            };

            wsRef.current = ws;
        } catch (error) {
            console.error("WebSocket connection failed:", error);
        }
    };

    useEffect(() => {
        connect();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                window.clearTimeout(reconnectTimeoutRef.current);
            }
            if (heartbeatIntervalRef.current) {
                window.clearInterval(heartbeatIntervalRef.current);
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [url]);

    return { isConnected, send: (data: any) => wsRef.current?.send(JSON.stringify(data)) };
}

