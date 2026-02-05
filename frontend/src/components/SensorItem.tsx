import React from "react";
import { ResponsiveContainer, AreaChart, Area } from "recharts";
import { useSensorTrend } from "../hooks/useLiveData";

interface SensorItemProps {
    sensor: any;
    liveValue: string | number;
    isExpanded: boolean;
    onToggle: () => void;
}

export const SensorItem: React.FC<SensorItemProps> = ({ sensor, liveValue, isExpanded, onToggle }) => {
    const valueNum = Number(liveValue);
    const isWarning = sensor.warning_threshold && valueNum >= sensor.warning_threshold;
    const isCritical = sensor.critical_threshold && valueNum >= sensor.critical_threshold;
    const { data: sensorTrend } = useSensorTrend(sensor?.id, "1h", 30);
    const trendData = sensorTrend?.points?.slice(-30).map((p: any) => ({ value: p.value })) || [];

    return (
        <div 
            className={`rounded-xl border p-4 transition-all ${
                isCritical 
                    ? "border-rose-500/50 bg-rose-500/10" 
                    : isWarning 
                    ? "border-amber-500/50 bg-amber-500/10"
                    : "border-slate-700/50 bg-slate-800/30"
            }`}
        >
            <button
                onClick={onToggle}
                className="w-full flex items-center justify-between text-left"
            >
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                        <p className="text-base font-semibold">{sensor.name}</p>
                        {(isWarning || isCritical) && (
                            <span className="text-xs">⚠️</span>
                        )}
                    </div>
                    <p className="text-xs text-slate-400">
                        {sensor.sensor_type || "sensor"} • {sensor.unit || "—"}
                    </p>
                    {/* Mini trend sparkline */}
                    {trendData.length > 0 && (
                        <div className="mt-2 h-[30px] w-full max-w-[120px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={trendData}>
                                    <defs>
                                        <linearGradient id={`spark-${sensor.id}`} x1="0" x2="0" y1="0" y2="1">
                                            <stop offset="0%" stopColor={isCritical ? "#ef4444" : isWarning ? "#f59e0b" : "#22d3ee"} stopOpacity={0.6} />
                                            <stop offset="100%" stopColor={isCritical ? "#ef4444" : isWarning ? "#f59e0b" : "#22d3ee"} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <Area
                                        type="monotone"
                                        dataKey="value"
                                        stroke={isCritical ? "#ef4444" : isWarning ? "#f59e0b" : "#22d3ee"}
                                        fill={`url(#spark-${sensor.id})`}
                                        strokeWidth={1.5}
                                        dot={false}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>
                <div className="text-right ml-4">
                    <p className={`text-2xl font-bold ${
                        isCritical ? "text-rose-300" : isWarning ? "text-amber-300" : "text-slate-200"
                    }`}>
                        {liveValue}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                        {sensor.unit || ""}
                    </p>
                </div>
            </button>
            {isExpanded && (
                <div className="mt-3 grid sm:grid-cols-2 gap-3 text-sm text-slate-300 pt-3 border-t border-slate-700/50">
                    <div className="rounded-lg bg-slate-900/60 border border-slate-700/50 p-3">
                        <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Thresholds</p>
                        <div className="space-y-1">
                            <p>Warn: <span className="text-amber-300">{sensor.warning_threshold ?? "—"}</span></p>
                            <p>Critical: <span className="text-rose-300">{sensor.critical_threshold ?? "—"}</span></p>
                        </div>
                    </div>
                    <div className="rounded-lg bg-slate-900/60 border border-slate-700/50 p-3">
                        <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Range</p>
                        <div className="space-y-1">
                            <p>Min: {sensor.min_threshold ?? "—"}</p>
                            <p>Max: {sensor.max_threshold ?? "—"}</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

