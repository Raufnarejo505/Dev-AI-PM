import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useAIStatus } from "../hooks/useLiveData";
import { useT } from "../i18n/I18nProvider";

type Status = "available" | "unavailable" | "error";

function StatusChip({ status, label }: { status: Status; label: string }) {
    const map = {
        available: "text-green-700 bg-green-50 ring-green-600/20",
        unavailable: "text-amber-700 bg-amber-50 ring-amber-600/20",
        error: "text-red-700 bg-red-50 ring-red-600/20",
    } as const;

    const icon = status === "available" ? (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 6L9 17l-5-5" />
        </svg>
    ) : status === "error" ? (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            <path d="M12 9v4" />
            <path d="M12 17h.01" />
        </svg>
    ) : (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 1v6m0 6v6m4.22-13.22l4.24 4.24M1.54 1.54l4.24 4.24M20.46 20.46l-4.24-4.24M1.54 20.46l4.24-4.24" />
        </svg>
    );

    return (
        <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ring-1 ${map[status]}`}
            role="status"
            aria-live="polite"
        >
            {icon}
            {label}
        </span>
    );
}

function UserMenu({ user, role, onLogout }: { user: any; role: string; onLogout: () => void }) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="relative">
            <button
                className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm shadow-sm hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
                onClick={() => setIsOpen(!isOpen)}
                aria-haspopup="menu"
                aria-expanded={isOpen}
            >
                <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                    <span className="text-sm font-medium text-purple-700">
                        {(user?.name || user?.email || 'U').charAt(0).toUpperCase()}
                    </span>
                </div>
                <span className="hidden sm:inline text-slate-700">{role}</span>
                <svg className="w-4 h-4 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M6 9l6 6 6-6" />
                </svg>
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-48 rounded-lg border border-slate-200 bg-white shadow-lg z-50">
                    <div className="px-4 py-3 border-b border-slate-100">
                        <div className="text-sm font-medium text-slate-900">Role: {role}</div>
                        <div className="text-xs text-slate-500 truncate">{user?.email || 'User'}</div>
                    </div>
                    <button
                        className="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 focus:bg-slate-50 focus:outline-none"
                        onClick={() => {
                            onLogout();
                            setIsOpen(false);
                        }}
                    >
                        Abmelden
                    </button>
                </div>
            )}
        </div>
    );
}

export default function Topbar({ onMenuClick }: { onMenuClick?: () => void }) {
    const { user, logout } = useAuth();
    const t = useT();
    const { data: aiStatus, isLoading: aiLoading } = useAIStatus();

    const aiStatusText = aiStatus?.status === "healthy" || aiStatus?.status === "operational"
        ? t("status.healthy")
        : aiStatus?.status
        ? aiStatus.status
        : t("status.unknown");

    const getKIStatus = (): Status => {
        if (aiLoading) return "unavailable";
        if (!aiStatus) return "unavailable";
        if (aiStatus.status === "healthy" || aiStatus.status === "operational") return "available";
        if (aiStatus.status === "error" || aiStatus.status === "degraded") return "error";
        return "unavailable";
    };

    return (
        <header className="mb-6">
            <div className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white/70 backdrop-blur-sm p-6 shadow-sm lg:flex-row lg:items-start lg:justify-between">
                {/* Left: brand + title */}
                <div>
                    <h1 className="text-2xl font-semibold text-transparent bg-clip-text bg-gradient-to-r from-purple-700 to-purple-500">
                        {t("app.name")}
                    </h1>
                    <div className="mt-1 text-[12px] font-medium uppercase tracking-wide text-slate-500">
                        {t("app.tagline")}
                    </div>
                </div>

                {/* Right: status + user */}
                <div className="flex items-center gap-3">
                    {onMenuClick && (
                        <button
                            type="button"
                            aria-label="Menü öffnen"
                            onClick={onMenuClick}
                            className="lg:hidden inline-flex items-center justify-center w-10 h-10 rounded-xl border border-slate-200 bg-white hover:bg-purple-50 transition-colors"
                        >
                            <svg className="w-5 h-5 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M4 6h16" />
                                <path d="M4 12h16" />
                                <path d="M4 18h16" />
                            </svg>
                        </button>
                    )}

                    <StatusChip 
                        status={getKIStatus()} 
                        label={`KI: ${aiLoading ? 'Loading' : aiStatusText}`} 
                    />

                    <UserMenu 
                        role={user?.role?.toUpperCase() || "ADMIN"} 
                        onLogout={logout} 
                        user={user} 
                    />
                </div>
            </div>
        </header>
    );
}

