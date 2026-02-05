import React from "react";
import { useQuery } from "@tanstack/react-query";
import { mqttApi } from "../api/mqtt";
import { useErrorToast } from "../components/ErrorToast";
import { StatusBadge } from "../components/StatusBadge";
import { CardSkeleton } from "../components/LoadingSkeleton";

export default function MQTTStatusPage() {
    const { ErrorComponent } = useErrorToast();

    const { data: status, isLoading } = useQuery({
        queryKey: ["mqtt", "status"],
        queryFn: () => mqttApi.getStatus(),
        refetchInterval: 10000,
    });

    if (isLoading) {
        return <CardSkeleton />;
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-100">MQTT Status</h1>
                <p className="text-slate-400 mt-1">Monitor MQTT broker and consumer status</p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6">
                    <h2 className="text-lg font-semibold text-slate-100 mb-4">Broker</h2>
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">Connection:</span>
                            <StatusBadge status={status?.connected ? "connected" : "disconnected"} />
                        </div>
                        {status?.broker && (
                            <>
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400">Host:</span>
                                    <span className="text-slate-200">{status.broker.host}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400">Port:</span>
                                    <span className="text-slate-200">{status.broker.port}</span>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6">
                    <h2 className="text-lg font-semibold text-slate-100 mb-4">Consumer</h2>
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-slate-400">Status:</span>
                            <StatusBadge status={status?.consumer?.connected ? "connected" : "disconnected"} />
                        </div>
                        {status?.consumer?.queue_size !== undefined && (
                            <div className="flex items-center justify-between">
                                <span className="text-slate-400">Queue Size:</span>
                                <span className="text-slate-200">{status.consumer.queue_size}</span>
                            </div>
                        )}
                        {status?.consumer?.topics && status.consumer.topics.length > 0 && (
                            <div>
                                <span className="text-slate-400 block mb-2">Topics:</span>
                                <div className="space-y-1">
                                    {status.consumer.topics.map((topic: string, idx: number) => (
                                        <div key={idx} className="text-sm text-slate-300 bg-slate-800/50 px-2 py-1 rounded">
                                            {topic}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {ErrorComponent}
        </div>
    );
}

