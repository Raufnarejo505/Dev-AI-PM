import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { sensorsApi } from "../api/sensors";
import { machinesApi } from "../api/machines";
import { SensorRead, SensorCreate } from "../types/api";
import { CardSkeleton, ListSkeleton } from "../components/LoadingSkeleton";
import { useErrorToast } from "../components/ErrorToast";
import { formatDateTime } from "../utils/formatters";
import { SensorModal } from "../components/SensorModal";
import { useT } from "../i18n/I18nProvider";

export default function SensorsPage() {
    const t = useT();
    const { showError, ErrorComponent } = useErrorToast();
    const queryClient = useQueryClient();
    const [selectedMachine, setSelectedMachine] = useState<string>("all");
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [selectedSensor, setSelectedSensor] = useState<SensorRead | null>(null);
    const [isEditing, setIsEditing] = useState(false);

    const { data: machines = [] } = useQuery({
        queryKey: ["machines"],
        queryFn: () => machinesApi.list(),
    });

    const { data: sensors = [], isLoading } = useQuery({
        queryKey: ["sensors", selectedMachine],
        queryFn: () => sensorsApi.list(selectedMachine === "all" ? undefined : selectedMachine),
        refetchInterval: 30000,
    });

    const createMutation = useMutation({
        mutationFn: (data: SensorCreate) => sensorsApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["sensors"] });
            setShowCreateModal(false);
            showError(t("sensors.toast.created"));
        },
        onError: (error: any) => {
            showError(`${t("sensors.toast.createFailed")} ${error.response?.data?.detail || error.message}`);
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<SensorCreate> }) => 
            sensorsApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["sensors"] });
            setIsEditing(false);
            setSelectedSensor(null);
            showError(t("sensors.toast.updated"));
        },
        onError: (error: any) => {
            showError(`${t("sensors.toast.updateFailed")} ${error.response?.data?.detail || error.message}`);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: (id: string) => sensorsApi.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["sensors"] });
            showError(t("sensors.toast.deleted"));
        },
        onError: (error: any) => {
            showError(`${t("sensors.toast.deleteFailed")} ${error.response?.data?.detail || error.message}`);
        },
    });

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-100">{t("sensors.title")}</h1>
                    <p className="text-slate-400 mt-1">{t("sensors.subtitle")}</p>
                </div>
                <div className="flex gap-3">
                    <select
                        value={selectedMachine}
                        onChange={(e) => setSelectedMachine(e.target.value)}
                        className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                    >
                        <option value="all">{t("sensors.allMachines")}</option>
                        {machines.map((m: any) => (
                            <option key={m.id} value={m.id}>
                                {m.name}
                            </option>
                        ))}
                    </select>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
                    >
                        {t("sensors.addSensor")}
                    </button>
                </div>
            </div>

            {isLoading ? (
                <ListSkeleton />
            ) : (
                <div className="grid gap-4">
                    {sensors.map((sensor: SensorRead) => (
                        <div
                            key={sensor.id}
                            className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6"
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-xl font-semibold text-slate-100">{sensor.name}</h3>
                                    <p className="text-sm text-slate-400">
                                        {sensor.sensor_type || t("sensors.sensorFallback")} • {sensor.unit || t("common.na")}
                                    </p>
                                    {sensor.latest_value !== undefined && (
                                        <p className="text-2xl font-bold text-emerald-400 mt-2">
                                            {sensor.latest_value} {sensor.unit || ""}
                                        </p>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => {
                                            setSelectedSensor(sensor);
                                            setIsEditing(true);
                                        }}
                                        className="px-3 py-1.5 text-sm bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                                    >
                                        {t("common.edit")}
                                    </button>
                                    <button
                                        onClick={() => {
                                            if (confirm(`${t("common.deleteConfirmPrefix")} ${sensor.name}?`)) {
                                                deleteMutation.mutate(sensor.id);
                                            }
                                        }}
                                        className="px-3 py-1.5 text-sm bg-rose-600/20 hover:bg-rose-600/30 text-rose-200 rounded-lg transition-colors"
                                    >
                                        {t("common.delete")}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <SensorModal
                isOpen={showCreateModal || isEditing}
                onClose={() => {
                    setShowCreateModal(false);
                    setIsEditing(false);
                    setSelectedSensor(null);
                }}
                onSave={(data) => {
                    if (isEditing && selectedSensor) {
                        updateMutation.mutate({ id: selectedSensor.id, data });
                    } else {
                        createMutation.mutate(data);
                    }
                }}
                sensor={selectedSensor}
                isEditing={isEditing}
                isLoading={createMutation.isPending || updateMutation.isPending}
                machines={machines}
            />

            {ErrorComponent}
        </div>
    );
}

