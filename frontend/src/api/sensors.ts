import api from "./index";
import { SensorCreate, SensorUpdate, SensorRead } from "../types/api";

export const sensorsApi = {
    // List sensors
    list: async (machineId?: string): Promise<SensorRead[]> => {
        const params = machineId ? `?machine_id=${machineId}` : "";
        const { data } = await api.get(`/sensors${params}`);
        return data;
    },

    // Get single sensor
    get: async (sensorId: string): Promise<SensorRead> => {
        const { data } = await api.get(`/sensors/${sensorId}`);
        return data;
    },

    // Create sensor
    create: async (payload: SensorCreate): Promise<SensorRead> => {
        const { data } = await api.post("/sensors", payload);
        return data;
    },

    // Update sensor
    update: async (sensorId: string, payload: SensorUpdate): Promise<SensorRead> => {
        const { data } = await api.patch(`/sensors/${sensorId}`, payload);
        return data;
    },

    // Delete sensor
    delete: async (sensorId: string): Promise<void> => {
        await api.delete(`/sensors/${sensorId}`);
    },

    // Get sensor trend
    getTrend: async (sensorId: string, interval: "1h" | "6h" | "24h" | "7d" | "30d" = "24h", points = 200) => {
        const { data } = await api.get(`/sensors/${sensorId}/trend?interval=${interval}&points=${points}`);
        return data;
    },
};

