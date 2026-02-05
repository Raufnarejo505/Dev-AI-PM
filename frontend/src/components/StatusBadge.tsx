import React from "react";

interface StatusBadgeProps {
    status: string;
    variant?: "default" | "outline";
    size?: "sm" | "md" | "lg";
}

export function StatusBadge({ status, variant = "default", size = "md" }: StatusBadgeProps) {
    const statusLower = status?.toLowerCase() || "";

    const getStatusStyles = () => {
        const isError = statusLower.includes("critical") || statusLower.includes("alarm") || statusLower === "offline";
        const isWarning = statusLower.includes("warning") || statusLower.includes("warn") || statusLower === "degraded";
        const isSuccess = statusLower === "online" || statusLower === "healthy" || statusLower === "normal" || statusLower === "active" || statusLower === "connected";

        if (isError) {
            return variant === "outline"
                ? "bg-transparent text-[#1F2937] border-[#EF4444]"
                : "bg-rose-50 text-[#1F2937] border-rose-200";
        }
        if (isWarning) {
            return variant === "outline"
                ? "bg-transparent text-[#1F2937] border-[#F59E0B]"
                : "bg-amber-50 text-[#1F2937] border-amber-200";
        }
        if (isSuccess) {
            return variant === "outline"
                ? "bg-transparent text-[#1F2937] border-[#22C55E]"
                : "bg-emerald-50 text-[#1F2937] border-emerald-200";
        }
        return variant === "outline"
            ? "bg-transparent text-[#1F2937] border-[#A78BFA]"
            : "bg-purple-50 text-[#1F2937] border-purple-200";
    };

    const sizeClasses = {
        sm: "text-xs px-2 py-0.5",
        md: "text-xs px-2.5 py-1",
        lg: "text-sm px-3 py-1.5",
    };

    return (
        <span
            className={`inline-flex items-center rounded-lg border font-medium ${getStatusStyles()} ${sizeClasses[size]}`}
        >
            {status}
        </span>
    );
}











