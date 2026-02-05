import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { aiApi } from "../api/ai";
import { useErrorToast } from "../components/ErrorToast";
import { StatusBadge } from "../components/StatusBadge";
import { CardSkeleton } from "../components/LoadingSkeleton";

export default function AIServicePage() {
    const { showError, ErrorComponent } = useErrorToast();
    const queryClient = useQueryClient();

    const { data: status, isLoading } = useQuery({
        queryKey: ["ai", "status"],
        queryFn: () => aiApi.getStatus(),
        refetchInterval: 10000,
    });

    const { data: logs = [] } = useQuery({
        queryKey: ["ai", "logs"],
        queryFn: () => aiApi.getLogs(50),
        refetchInterval: 30000,
    });

    const { data: models = [] } = useQuery({
        queryKey: ["ai", "models"],
        queryFn: () => aiApi.listModels(),
        refetchInterval: 60000,
    });

    const retrainMutation = useMutation({
        mutationFn: () => aiApi.triggerRetrain(),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["ai"] });
            showError("✅ Retrain job queued successfully!");
        },
        onError: (error: any) => {
            showError(`❌ Failed to trigger retrain: ${error.response?.data?.detail || error.message}`);
        },
    });

    if (isLoading) {
        return <CardSkeleton />;
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-100">AI Service</h1>
                    <p className="text-slate-400 mt-1">Monitor AI service status and models</p>
                </div>
                <button
                    onClick={() => retrainMutation.mutate()}
                    disabled={retrainMutation.isPending}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                    {retrainMutation.isPending ? "Queuing..." : "Trigger Retrain"}
                </button>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6">
                    <h2 className="text-lg font-semibold text-slate-100 mb-4">Service Status</h2>
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">Status:</span>
                            <StatusBadge status={status?.status || "unknown"} />
                        </div>
                        {status?.model_version && (
                            <div className="flex items-center justify-between">
                                <span className="text-slate-400">Model Version:</span>
                                <span className="text-slate-200">{status.model_version}</span>
                            </div>
                        )}
                        {status?.performance && (
                            <>
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400">Predictions Total:</span>
                                    <span className="text-slate-200">
                                        {status.performance.predictions_total?.toLocaleString()}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400">Avg Response Time:</span>
                                    <span className="text-slate-200">
                                        {status.performance.avg_response_time_ms?.toFixed(2)} ms
                                    </span>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6">
                    <h2 className="text-lg font-semibold text-slate-100 mb-4">Models</h2>
                    <div className="space-y-2">
                        {models.length === 0 ? (
                            <p className="text-slate-400">No models registered</p>
                        ) : (
                            models.map((model: any) => (
                                <div key={model.id} className="p-3 bg-slate-800/50 rounded-lg">
                                    <div className="font-semibold text-slate-200">{model.name}</div>
                                    <div className="text-sm text-slate-400">v{model.version}</div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-slate-100 mb-4">Recent Logs</h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                    {logs.map((log: any, idx: number) => (
                        <div key={idx} className="p-3 bg-slate-800/50 rounded-lg text-sm">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-slate-300">{log.action}</span>
                                <span className="text-slate-500 text-xs">
                                    {new Date(log.timestamp).toLocaleString()}
                                </span>
                            </div>
                            <p className="text-slate-400 text-xs">{log.details}</p>
                        </div>
                    ))}
                </div>
            </div>

            {ErrorComponent}
        </div>
    );
}

