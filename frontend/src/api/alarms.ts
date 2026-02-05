import api from "./index";
import { AlarmCreate, AlarmUpdate, AlarmRead, CommentCreate, CommentRead } from "../types/api";

export const alarmsApi = {
    // List alarms
    list: async (status?: string): Promise<AlarmRead[]> => {
        const params = status ? `?status=${status}` : "";
        const { data } = await api.get(`/alarms${params}`);
        return data;
    },

    // Create alarm
    create: async (payload: AlarmCreate): Promise<AlarmRead> => {
        const { data } = await api.post("/alarms", payload);
        return data;
    },

    // Get single alarm
    get: async (alarmId: string): Promise<AlarmRead> => {
        const { data } = await api.get(`/alarms/${alarmId}`);
        return data;
    },

    // Update alarm
    update: async (alarmId: string, payload: AlarmUpdate): Promise<AlarmRead> => {
        const { data } = await api.patch(`/alarms/${alarmId}`, payload);
        return data;
    },

    // Resolve alarm
    resolve: async (alarmId: string, resolutionNotes?: string): Promise<AlarmRead> => {
        const params = resolutionNotes ? `?resolution_notes=${encodeURIComponent(resolutionNotes)}` : "";
        const { data } = await api.post(`/alarms/${alarmId}/resolve${params}`);
        return data;
    },

    // Get alarms by prediction
    getByPrediction: async (predictionId: string): Promise<AlarmRead[]> => {
        const { data } = await api.get(`/alarms/prediction/${predictionId}`);
        return data;
    },

    // Bulk update alarms
    bulkUpdate: async (alarmIds: string[], payload: AlarmUpdate): Promise<void> => {
        await api.post(`/alarms/bulk?ids=${alarmIds.join(",")}`, [payload]);
    },

    // Add comment to alarm
    addComment: async (alarmId: string, payload: CommentCreate): Promise<CommentRead> => {
        const { data } = await api.post(`/alarms/${alarmId}/comments`, payload);
        return data;
    },

    // Get alarm comments
    getComments: async (alarmId: string): Promise<CommentRead[]> => {
        const { data } = await api.get(`/alarms/${alarmId}/comments`);
        return data;
    },
};

