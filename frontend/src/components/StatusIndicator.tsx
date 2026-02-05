import React from "react";

interface StatusIndicatorProps {
    status: "healthy" | "warning" | "critical" | "online" | "offline" | "degraded" | "maintenance";
    size?: "sm" | "md" | "lg";
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, size = "md" }) => {
    const statusMap: Record<string, { color: string }> = {
        healthy: { color: "bg-emerald-400" },
        online: { color: "bg-emerald-400" },
        warning: { color: "bg-amber-400" },
        degraded: { color: "bg-amber-400" },
        critical: { color: "bg-rose-400" },
        offline: { color: "bg-rose-400" },
        maintenance: { color: "bg-blue-400" },
    };

    const statusKey = status?.toLowerCase() || "offline";
    const statusInfo = statusMap[statusKey] || { color: "bg-slate-400" };

    const sizeClasses = {
        sm: "w-2 h-2",
        md: "w-3 h-3",
        lg: "w-4 h-4",
    };

    return (
        <span
            className={`inline-block rounded-full ${sizeClasses[size]} ${statusInfo.color}`}
            aria-label={status}
        />
    );
};

