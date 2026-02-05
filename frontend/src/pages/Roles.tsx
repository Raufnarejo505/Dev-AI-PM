import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { rolesApi } from "../api/roles";
import { RoleRead } from "../types/api";
import { useErrorToast } from "../components/ErrorToast";
import { CardSkeleton } from "../components/LoadingSkeleton";
import { formatDateTime } from "../utils/formatters";

export default function RolesPage() {
    const { showError, ErrorComponent } = useErrorToast();
    const queryClient = useQueryClient();
    const [showCreateModal, setShowCreateModal] = useState(false);

    const { data: roles = [], isLoading } = useQuery({
        queryKey: ["roles"],
        queryFn: () => rolesApi.list(),
        refetchInterval: 60000,
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => rolesApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["roles"] });
            showError("✅ Role deleted successfully!");
        },
        onError: (error: any) => {
            showError(`❌ Failed to delete role: ${error.response?.data?.detail || error.message}`);
        },
    });

    if (isLoading) {
        return <CardSkeleton />;
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-100">Roles</h1>
                    <p className="text-slate-400 mt-1">Manage user roles and permissions</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
                >
                    + Add Role
                </button>
            </div>

            <div className="grid gap-4">
                {roles.map((role: RoleRead) => (
                    <div
                        key={role.id}
                        className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <h3 className="text-xl font-semibold text-slate-100 mb-2">{role.name}</h3>
                                {role.description && (
                                    <p className="text-slate-400 mb-3">{role.description}</p>
                                )}
                                {role.permissions && role.permissions.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mb-3">
                                        {role.permissions.map((permission, idx) => (
                                            <span
                                                key={idx}
                                                className="text-xs px-2 py-1 bg-blue-500/20 text-blue-200 rounded border border-blue-400/40"
                                            >
                                                {permission}
                                            </span>
                                        ))}
                                    </div>
                                )}
                                <p className="text-xs text-slate-500">
                                    Created: {formatDateTime(role.created_at)}
                                </p>
                            </div>
                            <button
                                onClick={() => {
                                    if (confirm(`Delete ${role.name}?`)) {
                                        deleteMutation.mutate(role.id);
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

