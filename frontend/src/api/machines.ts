import api from "./index";
import { MachineCreate, MachineUpdate, MachineRead } from "../types/api";

export const machinesApi = {
    // List all machines
    list: async (limit?: number): Promise<MachineRead[]> => {
        const params = limit ? `?limit=${limit}` : "";
        const { data } = await api.get(`/machines${params}`);
        return data;
    },

    // Get single machine
    get: async (machineId: string): Promise<MachineRead> => {
        const { data } = await api.get(`/machines/${machineId}`);
        return data;
    },

    // Create machine
    create: async (payload: MachineCreate): Promise<MachineRead> => {
        const { data } = await api.post("/machines", payload);
        return data;
    },

    // Update machine
    update: async (machineId: string, payload: MachineUpdate): Promise<MachineRead> => {
        const { data } = await api.patch(`/machines/${machineId}`, payload);
        return data;
    },

    // Delete machine
    delete: async (machineId: string): Promise<void> => {
        await api.delete(`/machines/${machineId}`);
    },

    // Bulk create
    bulkCreate: async (payload: MachineCreate[]): Promise<MachineRead[]> => {
        const { data } = await api.post("/machines/bulk", payload);
        return data;
    },

    // Get machine summary
    getSummary: async (machineId: string) => {
        const { data } = await api.get(`/machines/${machineId}/summary`);
        return data;
    },

    // Get machine sensor data
    getSensorData: async (machineId: string, params?: {
        start_time?: string;
        end_time?: string;
        limit?: number;
    }) => {
        const queryParams = new URLSearchParams();
        if (params?.start_time) queryParams.append("start_time", params.start_time);
        if (params?.end_time) queryParams.append("end_time", params.end_time);
        if (params?.limit) queryParams.append("limit", params.limit.toString());
        const query = queryParams.toString();
        const { data } = await api.get(`/history/machines/${machineId}/sensor-data${query ? `?${query}` : ""}`);
        return data;
    },

    // Get machine predictions
    getPredictions: async (machineId: string, params?: {
        start_time?: string;
        end_time?: string;
        limit?: number;
    }) => {
        const queryParams = new URLSearchParams();
        if (params?.start_time) queryParams.append("start_time", params.start_time);
        if (params?.end_time) queryParams.append("end_time", params.end_time);
        if (params?.limit) queryParams.append("limit", params.limit.toString());
        const query = queryParams.toString();
        const { data } = await api.get(`/history/machines/${machineId}/predictions${query ? `?${query}` : ""}`);
        return data;
    },

    // Update machine thresholds
    updateThresholds: async (machineId: string, thresholds: any) => {
        const { data } = await api.patch(`/machines/${machineId}/thresholds`, thresholds);
        return data;
    },
};

