import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ticketsApi } from "../api/tickets";
import { machinesApi } from "../api/machines";
import { alarmsApi } from "../api/alarms";
import { TicketRead, TicketCreate } from "../types/api";
import { CardSkeleton, ListSkeleton } from "../components/LoadingSkeleton";
import { useErrorToast } from "../components/ErrorToast";
import { StatusBadge } from "../components/StatusBadge";
import { formatDateTime } from "../utils/formatters";
import { TicketModal } from "../components/TicketModal";
import { useT } from "../i18n/I18nProvider";

export default function TicketsPage() {
    const t = useT();
    const { showError, ErrorComponent } = useErrorToast();
    const queryClient = useQueryClient();
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [selectedTicket, setSelectedTicket] = useState<TicketRead | null>(null);
    const [isEditing, setIsEditing] = useState(false);

    const { data: machines = [] } = useQuery({
        queryKey: ["machines"],
        queryFn: () => machinesApi.list(),
    });

    const { data: alarms = [] } = useQuery({
        queryKey: ["alarms", "active"],
        queryFn: () => alarmsApi.list("active"),
    });

    const { data: tickets = [], isLoading } = useQuery({
        queryKey: ["tickets"],
        queryFn: () => ticketsApi.list(),
        refetchInterval: 30000,
    });

    const createMutation = useMutation({
        mutationFn: (data: TicketCreate) => ticketsApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tickets"] });
            setShowCreateModal(false);
            showError(t("tickets.toast.created"));
        },
        onError: (error: any) => {
            showError(`${t("tickets.toast.createFailed")} ${error.response?.data?.detail || error.message}`);
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<TicketCreate> }) => 
            ticketsApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["tickets"] });
            setIsEditing(false);
            setSelectedTicket(null);
            showError(t("tickets.toast.updated"));
        },
        onError: (error: any) => {
            showError(`${t("tickets.toast.updateFailed")} ${error.response?.data?.detail || error.message}`);
        },
    });

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-100">{t("tickets.title")}</h1>
                    <p className="text-slate-400 mt-1">{t("tickets.subtitle")}</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
                >
                    {t("tickets.create")}
                </button>
            </div>

            {isLoading ? (
                <ListSkeleton />
            ) : (
                <div className="space-y-4">
                    {tickets.map((ticket: TicketRead) => (
                        <div
                            key={ticket.id}
                            className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <h3 className="text-xl font-semibold text-slate-100 mb-2">
                                        {ticket.title}
                                    </h3>
                                    {ticket.description && (
                                        <p className="text-slate-400 mb-3">{ticket.description}</p>
                                    )}
                                    <div className="flex items-center gap-3">
                                        <StatusBadge status={ticket.status || "open"} />
                                        {ticket.priority && (
                                            <StatusBadge status={ticket.priority} />
                                        )}
                                        <span className="text-sm text-slate-400">
                                            {formatDateTime(ticket.created_at)}
                                        </span>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => {
                                            setSelectedTicket(ticket);
                                            setIsEditing(true);
                                        }}
                                        className="px-3 py-1.5 text-sm bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                                    >
                                        {t("common.edit")}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {tickets.length === 0 && !isLoading && (
                <div className="text-center py-12 text-slate-400">
                    <p>{t("tickets.empty")}</p>
                </div>
            )}

            <TicketModal
                isOpen={showCreateModal || isEditing}
                onClose={() => {
                    setShowCreateModal(false);
                    setIsEditing(false);
                    setSelectedTicket(null);
                }}
                onSave={(data) => {
                    if (isEditing && selectedTicket) {
                        updateMutation.mutate({ id: selectedTicket.id, data });
                    } else {
                        createMutation.mutate(data);
                    }
                }}
                ticket={selectedTicket}
                isEditing={isEditing}
                isLoading={createMutation.isPending || updateMutation.isPending}
                machines={machines}
                alarms={alarms}
            />

            {ErrorComponent}
        </div>
    );
}

