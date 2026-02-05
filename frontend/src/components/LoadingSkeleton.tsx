import React from "react";
import { useT } from "../i18n/I18nProvider";

/**
 * Loading skeleton components for better UX during page transitions
 * Prevents blank screens and improves perceived performance
 */
export function DashboardSkeleton() {
    return (
        <div className="space-y-6 animate-pulse">
            <div className="h-8 bg-slate-800 rounded w-1/3"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-32 bg-slate-800 rounded-2xl"></div>
                ))}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="h-72 bg-slate-800 rounded-2xl"></div>
                <div className="h-72 bg-slate-800 rounded-2xl"></div>
            </div>
        </div>
    );
}

export function CardSkeleton() {
    return (
        <div className="h-32 bg-slate-800 rounded-2xl animate-pulse"></div>
    );
}

export function TableSkeleton() {
    return (
        <div className="space-y-3 animate-pulse">
            <div className="h-12 bg-slate-800 rounded"></div>
            {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-16 bg-slate-800 rounded"></div>
            ))}
        </div>
    );
}

export function ListSkeleton() {
    return (
        <div className="space-y-3 animate-pulse">
            {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-16 bg-slate-800 rounded"></div>
            ))}
        </div>
    );
}

export function ChartSkeleton() {
    const t = useT();
    return (
        <div className="h-72 bg-slate-800 rounded-2xl animate-pulse flex items-center justify-center">
            <div className="text-slate-500">{t("charts.loadingChart")}</div>
        </div>
    );
}
