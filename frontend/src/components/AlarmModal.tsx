import React, { useState, useEffect } from "react";
import { Modal } from "./Modal";
import { AlarmCreate, AlarmRead } from "../types/api";

interface AlarmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (data: AlarmCreate) => void;
    alarm?: AlarmRead | null;
    isEditing?: boolean;
    isLoading?: boolean;
    machines: Array<{ id: string; name: string }>;
}

export function AlarmModal({ 
    isOpen, 
    onClose, 
    onSave, 
    alarm, 
    isEditing = false, 
    isLoading = false,
    machines 
}: AlarmModalProps) {
    const [formData, setFormData] = useState<AlarmCreate>({
        machine_id: machines[0]?.id || "",
        sensor_id: "",
        prediction_id: "",
        severity: "warning",
        message: "",
        status: "active",
        metadata: {},
    });

    useEffect(() => {
        if (alarm && isEditing) {
            setFormData({
                machine_id: alarm.machine_id || "",
                sensor_id: alarm.sensor_id || "",
                prediction_id: alarm.prediction_id || "",
                severity: alarm.severity || "warning",
                message: alarm.message || "",
                status: alarm.status || "active",
                metadata: alarm.metadata || {},
            });
        } else {
            setFormData({
                machine_id: machines[0]?.id || "",
                sensor_id: "",
                prediction_id: "",
                severity: "warning",
                message: "",
                status: "active",
                metadata: {},
            });
        }
    }, [alarm, isEditing, isOpen, machines]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.message.trim()) {
            alert("Message is required");
            return;
        }
        if (!formData.machine_id) {
            alert("Machine is required");
            return;
        }
        onSave(formData);
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={isEditing ? "Edit Alarm" : "Create Alarm"}
            size="md"
        >
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Machine <span className="text-rose-400">*</span>
                    </label>
                    <select
                        value={formData.machine_id}
                        onChange={(e) => setFormData({ ...formData, machine_id: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        required
                        disabled={isLoading || isEditing}
                    >
                        <option value="">Select a machine</option>
                        {machines.map((m) => (
                            <option key={m.id} value={m.id}>
                                {m.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Severity <span className="text-rose-400">*</span>
                    </label>
                    <select
                        value={formData.severity}
                        onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        required
                        disabled={isLoading}
                    >
                        <option value="warning">Warning</option>
                        <option value="critical">Critical</option>
                        <option value="info">Info</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Message <span className="text-rose-400">*</span>
                    </label>
                    <textarea
                        value={formData.message}
                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        rows={4}
                        required
                        disabled={isLoading}
                        placeholder="Describe the alarm condition..."
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Sensor ID (optional)
                    </label>
                    <input
                        type="text"
                        value={formData.sensor_id || ""}
                        onChange={(e) => setFormData({ ...formData, sensor_id: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        placeholder="sensor-id"
                        disabled={isLoading}
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Prediction ID (optional)
                    </label>
                    <input
                        type="text"
                        value={formData.prediction_id || ""}
                        onChange={(e) => setFormData({ ...formData, prediction_id: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        placeholder="prediction-id"
                        disabled={isLoading}
                    />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
                    <button
                        type="button"
                        onClick={onClose}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                        disabled={isLoading}
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors disabled:opacity-50"
                        disabled={isLoading}
                    >
                        {isLoading ? "Saving..." : isEditing ? "Update" : "Create"}
                    </button>
                </div>
            </form>
        </Modal>
    );
}

