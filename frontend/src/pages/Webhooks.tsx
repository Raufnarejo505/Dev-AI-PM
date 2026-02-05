import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { webhooksApi } from "../api/webhooks";
import { WebhookRead } from "../types/api";
import { useErrorToast } from "../components/ErrorToast";
import { StatusBadge } from "../components/StatusBadge";
import { CardSkeleton } from "../components/LoadingSkeleton";
import { formatDateTime } from "../utils/formatters";

export default function WebhooksPage() {
    const { showError, ErrorComponent } = useErrorToast();
    const queryClient = useQueryClient();
    const [showCreateModal, setShowCreateModal] = useState(false);

    const { data: webhooks = [], isLoading } = useQuery({
        queryKey: ["webhooks"],
        queryFn: () => webhooksApi.list(),
        refetchInterval: 30000,
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => webhooksApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["webhooks"] });
            showError("✅ Webhook deleted successfully!");
        },
        onError: (error: any) => {
            showError(`❌ Failed to delete webhook: ${error.response?.data?.detail || error.message}`);
        },
    });

    if (isLoading) {
        return <CardSkeleton />;
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-100">Webhooks</h1>
                    <p className="text-slate-400 mt-1">Manage webhook integrations</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
                >
                    + Add Webhook
                </button>
            </div>

            <div className="grid gap-4">
                {webhooks.map((webhook: WebhookRead) => (
                    <div
                        key={webhook.id}
                        className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                    <h3 className="text-xl font-semibold text-slate-100">{webhook.name}</h3>
                                    <StatusBadge status={webhook.is_active ? "active" : "inactive"} />
                                </div>
                                <p className="text-slate-400 mb-3 break-all">{webhook.url}</p>
                                {webhook.events && webhook.events.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mb-3">
                                        {webhook.events.map((event, idx) => (
                                            <span
                                                key={idx}
                                                className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-200 rounded border border-emerald-400/40"
                                            >
                                                {event}
                                            </span>
                                        ))}
                                    </div>
                                )}
                                <p className="text-xs text-slate-500">
                                    Created: {formatDateTime(webhook.created_at)}
                                </p>
                            </div>
                            <button
                                onClick={() => {
                                    if (confirm(`Delete ${webhook.name}?`)) {
                                        deleteMutation.mutate(webhook.id);
                                    }
                                }}
                                className="px-3 py-1.5 text-sm bg-rose-600/20 hover:bg-rose-600/30 text-rose-200 rounded-lg transition-colors"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {ErrorComponent}
        </div>
    );
}

