import api from "./index";
import { WebhookCreate, WebhookUpdate, WebhookRead } from "../types/api";

export const webhooksApi = {
    // List webhooks
    list: async (isActive?: boolean): Promise<WebhookRead[]> => {
        const params = isActive !== undefined ? `?is_active=${isActive}` : "";
        const { data } = await api.get(`/webhooks${params}`);
        return data;
    },

    // Get single webhook
    get: async (webhookId: string): Promise<WebhookRead> => {
        const { data } = await api.get(`/webhooks/${webhookId}`);
        return data;
    },

    // Create webhook
    create: async (payload: WebhookCreate): Promise<WebhookRead> => {
        const { data } = await api.post("/webhooks", payload);
        return data;
    },

    // Update webhook
    update: async (webhookId: string, payload: WebhookUpdate): Promise<WebhookRead> => {
        const { data } = await api.patch(`/webhooks/${webhookId}`, payload);
        return data;
    },

    // Delete webhook
    delete: async (webhookId: string): Promise<void> => {
        await api.delete(`/webhooks/${webhookId}`);
    },
};

