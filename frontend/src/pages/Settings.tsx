import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsApi } from "../api/settings";
import { SettingRead, SettingUpdate } from "../types/api";
import { useErrorToast } from "../components/ErrorToast";
import { CardSkeleton } from "../components/LoadingSkeleton";

export default function SettingsPage() {
    const { showError, ErrorComponent } = useErrorToast();
    const queryClient = useQueryClient();
    const [editingKey, setEditingKey] = useState<string | null>(null);
    const [editValue, setEditValue] = useState("");

    const { data: settings = [], isLoading } = useQuery({
        queryKey: ["settings"],
        queryFn: () => settingsApi.list(),
        refetchInterval: 60000,
    });

    const updateMutation = useMutation({
        mutationFn: ({ key, data }: { key: string; data: SettingUpdate }) =>
            settingsApi.update(key, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["settings"] });
            setEditingKey(null);
            showError("✅ Setting updated successfully!");
        },
        onError: (error: any) => {
            showError(`❌ Failed to update setting: ${error.response?.data?.detail || error.message}`);
        },
    });

    if (isLoading) {
        return <CardSkeleton />;
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-100">Settings</h1>
                <p className="text-slate-400 mt-1">Manage system settings</p>
            </div>

            <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6">
                <div className="space-y-4">
                    {settings.map((setting: SettingRead) => (
                        <div key={setting.key} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                            <div className="flex-1">
                                <div className="font-semibold text-slate-200">{setting.key}</div>
                                {setting.description && (
                                    <div className="text-sm text-slate-400 mt-1">{setting.description}</div>
                                )}
                                {editingKey === setting.key ? (
                                    <div className="flex items-center gap-2 mt-2">
                                        <input
                                            type="text"
                                            value={editValue}
                                            onChange={(e) => setEditValue(e.target.value)}
                                            className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-slate-200"
                                        />
                                        <button
                                            onClick={() => {
                                                updateMutation.mutate({ key: setting.key, data: { value: editValue } });
                                            }}
                                            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg"
                                        >
                                            Save
                                        </button>
                                        <button
                                            onClick={() => {
                                                setEditingKey(null);
                                                setEditValue("");
                                            }}
                                            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                ) : (
                                    <div className="text-sm text-slate-300 mt-1">{setting.value}</div>
                                )}
                            </div>
                            {editingKey !== setting.key && (
                                <button
                                    onClick={() => {
                                        setEditingKey(setting.key);
                                        setEditValue(setting.value);
                                    }}
                                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-sm"
                                >
                                    Edit
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {ErrorComponent}
        </div>
    );
}

