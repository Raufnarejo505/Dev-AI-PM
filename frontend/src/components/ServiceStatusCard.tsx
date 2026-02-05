import React from "react";
import { useAIStatus } from "../hooks/useLiveData";
import { useT } from "../i18n/I18nProvider";

interface ServiceStatusCardProps {
    label: string;
}

export default function ServiceStatusCard({ label }: ServiceStatusCardProps) {
    const { data: aiStatus } = useAIStatus();
    const t = useT();

    const getStatus = () => {
        if (label === "AI Service") {
            const status = aiStatus?.status || "unknown";
            const isHealthy = status === "healthy" || status === "operational";
            return {
                status: isHealthy ? t("status.healthy") : status === "unknown" ? t("status.unknown") : status,
                color: isHealthy
                    ? "bg-emerald-50 border-emerald-200 text-[#1F2937]"
                    : "bg-rose-50 border-rose-200 text-[#1F2937]",
            };
        }
        return { status: t("status.unknown"), color: "bg-purple-50 border-purple-200 text-[#1F2937]" };
    };

    const { status, color } = getStatus();

    const displayLabel = label === "AI Service" ? t("nav.aiService") : label;

    return (
        <div className={`px-5 py-3 rounded-2xl border ${color} text-sm font-medium shadow-sm`}>
            <p className="text-xs uppercase tracking-[0.3em] text-[#9CA3AF] mb-1">{displayLabel}</p>
            <p className="text-lg font-semibold text-[#1F2937]">{status}</p>
        </div>
    );
}











