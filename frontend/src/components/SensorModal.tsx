import React, { useState, useEffect } from "react";
import { Modal } from "./Modal";
import { SensorCreate, SensorRead } from "../types/api";

interface SensorModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (data: SensorCreate) => void;
    sensor?: SensorRead | null;
    isEditing?: boolean;
    isLoading?: boolean;
    machines: Array<{ id: string; name: string }>;
}

export function SensorModal({ 
    isOpen, 
    onClose, 
    onSave, 
    sensor, 
    isEditing = false, 
    isLoading = false,
    machines 
}: SensorModalProps) {
    const [formData, setFormData] = useState<SensorCreate>({
        name: "",
        sensor_type: "",
        unit: "",
        machine_id: machines[0]?.id || "",
        min_threshold: undefined,
        max_threshold: undefined,
        warning_threshold: undefined,
        critical_threshold: undefined,
        metadata: {},
    });

    useEffect(() => {
        if (sensor && isEditing) {
            setFormData({
                name: sensor.name || "",
                sensor_type: sensor.sensor_type || "",
                unit: sensor.unit || "",
                machine_id: sensor.machine_id || "",
                min_threshold: sensor.min_threshold,
                max_threshold: sensor.max_threshold,
                warning_threshold: sensor.warning_threshold,
                critical_threshold: sensor.critical_threshold,
                metadata: sensor.metadata || {},
            });
        } else {
            setFormData({
                name: "",
                sensor_type: "",
                unit: "",
                machine_id: machines[0]?.id || "",
                min_threshold: undefined,
                max_threshold: undefined,
                warning_threshold: undefined,
                critical_threshold: undefined,
                metadata: {},
            });
        }
    }, [sensor, isEditing, isOpen, machines]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.name.trim()) {
            alert("Name is required");
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
            title={isEditing ? "Edit Sensor" : "Add Sensor"}
            size="md"
        >
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Name <span className="text-rose-400">*</span>
                    </label>
                    <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        required
                        disabled={isLoading}
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Sensor Type
                        </label>
                        <input
                            type="text"
                            value={formData.sensor_type}
                            onChange={(e) => setFormData({ ...formData, sensor_type: e.target.value })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            placeholder="temperature, pressure, vibration"
                            disabled={isLoading}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Unit
                        </label>
                        <input
                            type="text"
                            value={formData.unit}
                            onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            placeholder="°C, psi, rpm"
                            disabled={isLoading}
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        Machine <span className="text-rose-400">*</span>
                    </label>
                    <select
                        value={formData.machine_id}
                        onChange={(e) => setFormData({ ...formData, machine_id: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        required
                        disabled={isLoading}
                    >
                        <option value="">Select a machine</option>
                        {machines.map((m) => (
                            <option key={m.id} value={m.id}>
                                {m.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Min Threshold
                        </label>
                        <input
                            type="number"
                            step="any"
                            value={formData.min_threshold ?? ""}
                            onChange={(e) => setFormData({ 
                                ...formData, 
                                min_threshold: e.target.value ? parseFloat(e.target.value) : undefined 
                            })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            disabled={isLoading}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Max Threshold
                        </label>
                        <input
                            type="number"
                            step="any"
                            value={formData.max_threshold ?? ""}
                            onChange={(e) => setFormData({ 
                                ...formData, 
                                max_threshold: e.target.value ? parseFloat(e.target.value) : undefined 
                            })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            disabled={isLoading}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Warning Threshold
                        </label>
                        <input
                            type="number"
                            step="any"
                            value={formData.warning_threshold ?? ""}
                            onChange={(e) => setFormData({ 
                                ...formData, 
                                warning_threshold: e.target.value ? parseFloat(e.target.value) : undefined 
                            })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            disabled={isLoading}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Critical Threshold
                        </label>
                        <input
                            type="number"
                            step="any"
                            value={formData.critical_threshold ?? ""}
                            onChange={(e) => setFormData({ 
                                ...formData, 
                                critical_threshold: e.target.value ? parseFloat(e.target.value) : undefined 
                            })}
                            className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                            disabled={isLoading}
                        />
                    </div>
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

