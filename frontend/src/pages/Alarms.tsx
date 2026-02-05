import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { alarmsApi } from "../api/alarms";
import { machinesApi } from "../api/machines";
import { AlarmRead, CommentCreate, AlarmCreate } from "../types/api";
import { CardSkeleton, ListSkeleton } from "../components/LoadingSkeleton";
import { useErrorToast } from "../components/ErrorToast";
import { StatusBadge } from "../components/StatusBadge";
import { formatDateTime, formatRelativeTime } from "../utils/formatters";
import { AlarmModal } from "../components/AlarmModal";

export default function AlarmsPage() {
    const { showError, ErrorComponent } = useErrorToast();
    const queryClient = useQueryClient();
    const [filter, setFilter] = useState<"all" | "active" | "resolved">("all");
    const [selectedAlarm, setSelectedAlarm] = useState<AlarmRead | null>(null);
    const [commentText, setCommentText] = useState("");
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [isEditing, setIsEditing] = useState(false);

    const { data: machines = [] } = useQuery({
        queryKey: ["machines"],
        queryFn: () => machinesApi.list(),
    });

    const { data: alarms = [], isLoading } = useQuery({
        queryKey: ["alarms"],
        queryFn: () => alarmsApi.list(),
        refetchInterval: 8000,
    });

    const filteredAlarms = filter === "all"
        ? alarms
        : alarms.filter((a: AlarmRead) => 
            filter === "active" ? (a.status === "open" || a.status === "acknowledged") : a.status === "resolved"
        );

    const resolveMutation = useMutation({
        mutationFn: ({ id, notes }: { id: string; notes?: string }) => 
            alarmsApi.resolve(id, notes),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alarms"] });
            showError("✅ Alarm resolved successfully!");
        },
    });

    const commentMutation = useMutation({
        mutationFn: ({ alarmId, comment }: { alarmId: string; comment: CommentCreate }) =>
            alarmsApi.addComment(alarmId, comment),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alarms"] });
            setCommentText("");
            showError("✅ Comment added successfully!");
        },
    });

    const createMutation = useMutation({
        mutationFn: (data: AlarmCreate) => alarmsApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["alarms"] });
            setShowCreateModal(false);
            showError("✅ Alarm created successfully!");
        },
        onError: (error: any) => {
            showError(`❌ Failed to create alarm: ${error.response?.data?.detail || error.message}`);
        },
    });

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-100">Alarms</h1>
                    <p className="text-slate-400 mt-1">Monitor and manage system alarms</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
                    >
                        + Create Alarm
                    </button>
                    <button
                        onClick={() => setFilter("all")}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                            filter === "all"
                                ? "bg-emerald-600 text-white"
                                : "bg-slate-800 text-slate-300"
                        }`}
                    >
                        All
                    </button>
                    <button
                        onClick={() => setFilter("active")}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                            filter === "active"
                                ? "bg-rose-600 text-white"
                                : "bg-slate-800 text-slate-300"
                        }`}
                    >
                        Active
                    </button>
                    <button
                        onClick={() => setFilter("resolved")}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                            filter === "resolved"
                                ? "bg-slate-600 text-white"
                                : "bg-slate-800 text-slate-300"
                        }`}
                    >
                        Resolved
                    </button>
                </div>
            </div>

            {isLoading ? (
                <ListSkeleton />
            ) : filteredAlarms.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                    <p>No alarms found. {filter === "all" ? "" : `Try selecting "All" to see all alarms.`}</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {filteredAlarms.map((alarm: AlarmRead) => (
                        <div
                            key={alarm.id}
                            className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <StatusBadge status={alarm.severity || "warning"} />
                                        <StatusBadge status={alarm.status || "open"} />
                                    </div>
                                    <h3 className="text-lg font-semibold text-slate-100 mb-2">
                                        {alarm.message}
                                    </h3>
                                    <p className="text-sm text-slate-400">
                                        {formatRelativeTime(alarm.triggered_at || alarm.created_at)}
                                    </p>
                                </div>
                                {(alarm.status === "open" || alarm.status === "acknowledged") && (
                                    <button
                                        onClick={() => {
                                            if (confirm("Resolve this alarm?")) {
                                                resolveMutation.mutate({ id: alarm.id });
                                            }
                                        }}
                                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
                                    >
                                        Resolve
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <AlarmModal
                isOpen={showCreateModal || isEditing}
                onClose={() => {
                    setShowCreateModal(false);
                    setIsEditing(false);
                    setSelectedAlarm(null);
                }}
                onSave={(data) => {
                    if (isEditing && selectedAlarm) {
                        // Update not implemented in API, but we can resolve
                        showError("⚠️ Use the Resolve button to update alarm status");
                    } else {
                        createMutation.mutate(data);
                    }
                }}
                alarm={selectedAlarm}
                isEditing={isEditing}
                isLoading={createMutation.isPending}
                machines={machines}
            />

            {ErrorComponent}
        </div>
    );
}

