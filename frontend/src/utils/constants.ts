// API Constants
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const WS_BASE_URL = API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://");

// Refresh Intervals
export const REFRESH_INTERVALS = {
    DASHBOARD: 8000,      // 8 seconds
    REAL_TIME: 2000,      // 2 seconds
    STANDARD: 30000,      // 30 seconds
    SLOW: 60000,          // 60 seconds
};

// Chart Configuration
export const CHART_COLORS = {
    primary: "#22d3ee",
    secondary: "#10b981",
    warning: "#f59e0b",
    danger: "#ef4444",
    success: "#10b981",
    info: "#3b82f6",
};

// Status Colors
export const STATUS_COLORS = {
    online: "emerald",
    offline: "rose",
    degraded: "amber",
    maintenance: "blue",
    healthy: "emerald",
    warning: "amber",
    critical: "rose",
};

// Date Formats
export const DATE_FORMATS = {
    dateTime: "YYYY-MM-DD HH:mm:ss",
    date: "YYYY-MM-DD",
    time: "HH:mm:ss",
};

