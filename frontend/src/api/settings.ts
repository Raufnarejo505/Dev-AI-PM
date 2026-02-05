import api from "./index";
import { SettingCreate, SettingUpdate, SettingRead } from "../types/api";

export const settingsApi = {
    // List settings
    list: async (category?: string): Promise<SettingRead[]> => {
        const params = category ? `?category=${category}` : "";
        const { data } = await api.get(`/settings${params}`);
        return data;
    },

    // Get single setting
    get: async (key: string): Promise<SettingRead> => {
        const { data } = await api.get(`/settings/${key}`);
        return data;
    },

    // Create setting
    create: async (payload: SettingCreate): Promise<SettingRead> => {
        const { data } = await api.post("/settings", payload);
        return data;
    },

    // Update setting
    update: async (key: string, payload: SettingUpdate): Promise<SettingRead> => {
        const { data } = await api.patch(`/settings/${key}`, payload);
        return data;
    },
};

