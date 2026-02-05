import { useQuery } from "@tanstack/react-query";
import api from "../api";
import { useAuth } from "../contexts/AuthContext";

// Use a much longer refresh interval to prevent page freezing
const REFRESH_MS = 60000; // 60 seconds - prevent overload

// Dashboard Overview
export const useDashboardOverview = () => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["dashboard", "overview"],
        queryFn: async () => {
            try {
                const { data } = await api.get("/dashboard/overview");
                // Backend returns nested structure: { machines: { total, online }, alarms: { active }, ... }
                return {
                    machinesCount: data?.machines?.total || 0,
                    machinesOnline: data?.machines?.online || 0,
                    activeAlarms: data?.alarms?.active || 0,
                    sensorsTotal: data?.sensors?.total || 0,
                    predictionsLast24h: data?.predictions?.last_24h || 0,
                    // Computed fields
                    anomalyRate: 0, // Will be computed from predictions
                };
            } catch (error: any) {
                console.error("Dashboard overview fetch error:", error);
                return {
                    machinesCount: 0,
                    machinesOnline: 0,
                    activeAlarms: 0,
                    sensorsTotal: 0,
                    predictionsLast24h: 0,
                    anomalyRate: 0,
                };
            }
        },
        enabled: isAuthenticated,
        refetchInterval: REFRESH_MS * 2, // Refresh every 2 minutes
        staleTime: 30000, // Cache for 30 seconds
        retry: 0, // No retries to prevent blocking
        gcTime: 120000, // Garbage collect after 2 minutes
    });
};

// Machines
export const useMachines = (limit = 10) => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["machines", limit],
        queryFn: async () => {
            try {
                const { data } = await api.get(`/machines?limit=${limit}`, { timeout: 5000 });
                return Array.isArray(data) ? data : [];
            } catch (error: any) {
                console.error("Machines fetch error:", error);
                return [];
            }
        },
        enabled: isAuthenticated,
        refetchInterval: REFRESH_MS * 3, // Refresh every 3 minutes
        staleTime: 60000, // Cache for 1 minute
        retry: 0,
        gcTime: 180000,
    });
};

// Machine Summary
export const useMachineSummary = (machineId?: string) => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["machines", machineId, "summary"],
        queryFn: async () => {
            const { data } = await api.get(`/machines/${machineId}/summary`);
            return data;
        },
        enabled: isAuthenticated && Boolean(machineId),
        refetchInterval: REFRESH_MS,
        retry: 2,
    });
};

// Machine Sensor Data (time series)
export const useMachineSensorData = (
    machineId?: string,
    start?: string,
    end?: string,
    agg = "1m"
) => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["machines", machineId, "sensor-data", start, end, agg],
        queryFn: async () => {
            const params = new URLSearchParams({ agg });
            if (start) params.append("start", start);
            if (end) params.append("end", end);
            const { data } = await api.get(`/machines/${machineId}/sensor-data?${params}`);
            return Array.isArray(data) ? data : [];
        },
        enabled: isAuthenticated && Boolean(machineId),
        refetchInterval: REFRESH_MS,
        retry: 2,
    });
};

// Alarms
export const useAlarms = (status?: string) => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["alarms", status],
        queryFn: async () => {
            try {
                const params = status ? `?status=${status}` : "";
                const { data } = await api.get(`/alarms${params}`);
                return Array.isArray(data) ? data : [];
            } catch (error: any) {
                console.error("Alarms fetch error:", error);
                return [];
            }
        },
        enabled: isAuthenticated,
        refetchInterval: REFRESH_MS,
        retry: 2,
    });
};

// Tickets
export const useTickets = () => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["tickets"],
        queryFn: async () => {
            try {
                const { data } = await api.get("/tickets");
                return Array.isArray(data) ? data : [];
            } catch (error: any) {
                console.error("Tickets fetch error:", error);
                return [];
            }
        },
        enabled: isAuthenticated,
        refetchInterval: REFRESH_MS * 2,
        retry: 2,
    });
};

// Predictions
export const usePredictions = (limit = 50, sort = "desc") => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["predictions", limit, sort],
        queryFn: async () => {
            try {
                const { data } = await api.get(`/predictions?limit=${limit}&sort=${sort}`, {
                    timeout: 8000, // 8 second timeout
                });
                return Array.isArray(data) ? data : [];
            } catch (error: any) {
                console.error("Predictions fetch error:", error);
                return [];
            }
        },
        enabled: isAuthenticated,
        // Predictions are heavy; refresh much less often
        refetchInterval: REFRESH_MS * 3, // Refresh every 3 minutes
        staleTime: 60000, // Cache for 1 minute
        retry: 0, // No retries
        gcTime: 180000, // Garbage collect after 3 minutes
    });
};

// Sensors
export const useSensors = (machineId?: string) => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["sensors", machineId],
        queryFn: async () => {
            const url = machineId ? `/sensors?machine_id=${machineId}` : "/sensors";
            const { data } = await api.get(url);
            return Array.isArray(data) ? data : [];
        },
        enabled: isAuthenticated && Boolean(machineId),
        refetchInterval: REFRESH_MS,
        retry: 2,
    });
};

// Sensor Trend
export const useSensorTrend = (sensorId?: string, interval = "24h", points = 200) => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["sensors", sensorId, "trend", interval, points],
        queryFn: async () => {
            const { data } = await api.get(
                `/sensors/${sensorId}/trend?interval=${interval}&points=${points}`
            );
            return data;
        },
        enabled: isAuthenticated && Boolean(sensorId),
        refetchInterval: REFRESH_MS,
        retry: 2,
    });
};

// Machine Predictions
export const useMachinePredictions = (machineId?: string) => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["predictions", machineId],
        queryFn: async () => {
            const { data } = await api.get(`/machines/${machineId}/predictions`);
            return Array.isArray(data) ? data : [];
        },
        enabled: isAuthenticated && Boolean(machineId),
        refetchInterval: REFRESH_MS,
        retry: 2,
    });
};

// AI Status
export const useAIStatus = () => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["ai", "status"],
        queryFn: async () => {
            try {
                const { data } = await api.get("/ai/status");
                return data;
            } catch (error: any) {
                console.error("Error fetching AI status:", error);
                return { status: "unavailable", model_loaded: false };
            }
        },
        enabled: isAuthenticated,
        refetchInterval: REFRESH_MS * 2,
        retry: 2,
    });
};

// MQTT Status
export const useMQTTStatus = () => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["mqtt", "status"],
        queryFn: async () => {
            try {
                const { data } = await api.get("/mqtt/status");
                return data;
            } catch (error: any) {
                console.error("Error fetching MQTT status:", error);
                return { connected: false };
            }
        },
        enabled: isAuthenticated,
        refetchInterval: REFRESH_MS * 2,
        retry: 2,
    });
};

// OPC UA Status
export const useOPCUAStatus = () => {
    const { isAuthenticated } = useAuth();
    
    return useQuery({
        queryKey: ["opcua", "status"],
        queryFn: async () => {
            try {
                const { data } = await api.get("/opcua/status");
                return data;
            } catch (error: any) {
                console.error("OPC UA status fetch error:", error);
                return {
                    connected: false,
                    heartbeat_ts: null,
                    node_count: 0,
                    last_error: error?.response?.data?.detail || "Failed to fetch status",
                    sources: [],
                };
            }
        },
        enabled: isAuthenticated,
        refetchInterval: REFRESH_MS,
        retry: 2,
    });
};
