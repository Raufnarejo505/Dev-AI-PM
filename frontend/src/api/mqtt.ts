import api from "./index";
import { MQTTStatus } from "../types/api";

export const mqttApi = {
    // Get MQTT status
    getStatus: async (): Promise<MQTTStatus> => {
        const { data } = await api.get("/mqtt/status");
        return data;
    },
};

