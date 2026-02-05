import api from "./index";
import { AIStatus } from "../types/api";

export const aiApi = {
    // Get AI status
    getStatus: async (): Promise<AIStatus> => {
        const { data } = await api.get("/ai/status");
        return data;
    },

    // Trigger retrain
    triggerRetrain: async () => {
        const { data } = await api.post("/ai/retrain");
        return data;
    },

    // Get AI logs
    getLogs: async (limit = 100) => {
        const { data } = await api.get(`/ai/logs?limit=${limit}`);
        return data;
    },

    // List models
    listModels: async () => {
        const { data } = await api.get("/ai/models");
        return data;
    },

    // Register model
    registerModel: async (payload: { name: string; version: string; description?: string; path?: string }) => {
        const { data } = await api.post("/ai/models", payload);
        return data;
    },

    // Activate model
    activateModel: async (version: string) => {
        const { data } = await api.post(`/ai/models/${version}/activate`);
        return data;
    },

    // Rollback model
    rollbackModel: async (version: string) => {
        const { data } = await api.post(`/ai/models/${version}/rollback`);
        return data;
    },
};

