import api from "./index";

export const healthApi = {
    // Basic health check
    check: async () => {
        const { data } = await api.get("/health");
        return data;
    },

    // Liveness probe
    live: async () => {
        const { data } = await api.get("/health/live");
        return data;
    },

    // Readiness probe
    ready: async () => {
        const { data } = await api.get("/health/ready");
        return data;
    },
};

