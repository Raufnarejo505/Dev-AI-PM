import React from "react";

interface CardProps {
    title?: string;
    children: React.ReactNode;
    className?: string;
    headerAction?: React.ReactNode;
}

export function Card({ title, children, className = "", headerAction }: CardProps) {
    return (
        <div className={`bg-white/90 border border-slate-200 rounded-2xl p-6 shadow-sm backdrop-blur ${className}`}>
            {title && (
                <header className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
                    {headerAction}
                </header>
            )}
            {children}
        </div>
    );
}

interface KPICardProps {
    label: string;
    value: string | number;
    change?: string;
    trend?: "up" | "down" | "neutral";
    icon?: React.ReactNode;
    color?: string;
}

export function KPICard({ label, value, change, trend = "neutral", icon, color = "emerald" }: KPICardProps) {
    const colorClasses: Record<string, string> = {
        emerald: "from-emerald-50 to-emerald-100 text-slate-900 border border-emerald-200",
        rose: "from-rose-50 to-rose-100 text-slate-900 border border-rose-200",
        sky: "from-sky-50 to-sky-100 text-slate-900 border border-sky-200",
        amber: "from-amber-50 to-amber-100 text-slate-900 border border-amber-200",
        purple: "from-purple-50 to-purple-100 text-slate-900 border border-purple-200",
    };

    const trendIcon = trend === "up" ? "↑" : trend === "down" ? "↓" : "";

    return (
        <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-2xl p-6 shadow-sm`}>
            <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                    {icon && <div className="text-2xl">{icon}</div>}
                    <span className="text-sm font-medium opacity-90">{label}</span>
                </div>
            </div>
            <div className="text-3xl font-bold mb-1">{value}</div>
            {change && (
                <div className="text-xs opacity-80 flex items-center gap-1">
                    <span>{trendIcon}</span>
                    <span>{change}</span>
                </div>
            )}
        </div>
    );
}











