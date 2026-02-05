import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { machinesApi } from "../api/machines";
import { MachineRead, MachineCreate } from "../types/api";
import { CardSkeleton, ListSkeleton } from "../components/LoadingSkeleton";
import { StatusBadge } from "../components/StatusBadge";
import { StatusIndicator } from "../components/StatusIndicator";
import { useErrorToast } from "../components/ErrorToast";
import { formatDateTime } from "../utils/formatters";
import { MachineModal } from "../components/MachineModal";
import api from "../api";

export default function MachinesPage() {
    const { showError, ErrorComponent } = useErrorToast();
    const queryClient = useQueryClient();
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [selectedMachine, setSelectedMachine] = useState<MachineRead | null>(null);
    const [isEditing, setIsEditing] = useState(false);

    const { data: machines = [], isLoading } = useQuery({
        queryKey: ["machines"],
        queryFn: () => machinesApi.list(),
        refetchInterval: 30000,
        staleTime: 0, // Always consider data stale to force refresh
        gcTime: 0, // Don't cache data
    });

    const createMutation = useMutation({
        mutationFn: (data: MachineCreate) => machinesApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["machines"] });
            setShowCreateModal(false);
            showError("✅ Machine created successfully!");
        },
        onError: (error: any) => {
            showError(`❌ Failed to create machine: ${error.response?.data?.detail || error.message}`);
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<MachineCreate> }) => 
            machinesApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["machines"] });
            setIsEditing(false);
            setSelectedMachine(null);
            showError("✅ Machine updated successfully!");
        },
        onError: (error: any) => {
            showError(`❌ Failed to update machine: ${error.response?.data?.detail || error.message}`);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => machinesApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["machines"] });
            showError("✅ Machine deleted successfully!");
        },
        onError: (error: any) => {
            showError(`❌ Failed to delete machine: ${error.response?.data?.detail || error.message}`);
        },
    });

    if (isLoading) {
        return (
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-slate-100">Machines</h1>
                </div>
                <ListSkeleton />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-100">Machines</h1>
                    <p className="text-slate-400 mt-1">Manage and monitor all machines</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
                >
                    + Add Machine
                </button>
            </div>

            <div className="grid gap-4">
                {machines.map((machine: MachineRead) => (
                    <div
                        key={machine.id}
                        className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6 hover:border-emerald-500/40 transition-colors"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <StatusIndicator 
                                    status={machine.status as any || "offline"} 
                                    size="lg" 
                                />
                                <div>
                                    <h3 className="text-xl font-semibold text-slate-100">{machine.name}</h3>
                                    <p className="text-sm text-slate-400">{machine.location || "No location"}</p>
                                    {machine.criticality && (
                                        <span className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block ${
                                            machine.criticality.toLowerCase() === "high"
                                                ? "bg-rose-500/20 text-rose-200 border border-rose-400/40"
                                                : machine.criticality.toLowerCase() === "medium"
                                                ? "bg-amber-500/20 text-amber-200 border border-amber-400/40"
                                                : "bg-emerald-500/20 text-emerald-200 border border-emerald-400/40"
                                        }`}>
                                            {machine.criticality}
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <StatusBadge status={machine.status || "offline"} />
                                <button
                                    onClick={() => {
                                        setSelectedMachine(machine);
                                        setIsEditing(true);
                                    }}
                                    className="px-3 py-1.5 text-sm bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                                >
                                    Edit
                                </button>
                                <button
                                    onClick={() => {
                                        if (confirm(`Delete ${machine.name}?`)) {
                                            deleteMutation.mutate(machine.id);
                                        }
                                    }}
                                    className="px-3 py-1.5 text-sm bg-rose-600/20 hover:bg-rose-600/30 text-rose-200 rounded-lg transition-colors"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                        {machine.description && (
                            <p className="text-sm text-slate-400 mt-3">{machine.description}</p>
                        )}
                        <div className="mt-4 text-xs text-slate-500">
                            Created: {formatDateTime(machine.created_at)}
                        </div>
                    </div>
                ))}
            </div>

            {machines.length === 0 && (
                <div className="text-center py-12 text-slate-400">
                    <p>No machines found. Create your first machine to get started.</p>
                </div>
            )}

            <MachineModal
                isOpen={showCreateModal || isEditing}
                onClose={() => {
                    setShowCreateModal(false);
                    setIsEditing(false);
                    setSelectedMachine(null);
                }}
                onSave={(data) => {
                    if (isEditing && selectedMachine) {
                        updateMutation.mutate({ id: selectedMachine.id, data });
                    } else {
                        createMutation.mutate(data);
                    }
                }}
                machine={selectedMachine}
                isEditing={isEditing}
                isLoading={createMutation.isPending || updateMutation.isPending}
            />

            {ErrorComponent}
        </div>
    );
}

