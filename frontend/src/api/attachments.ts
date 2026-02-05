import api from "./index";

export const attachmentsApi = {
    // Upload attachment
    upload: async (file: File, resourceType: string, resourceId?: string) => {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("resource_type", resourceType);
        if (resourceId) formData.append("resource_id", resourceId);

        const { data } = await api.post("/attachments", formData, {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });
        return data;
    },

    // Get attachment
    get: async (attachmentId: string) => {
        const { data } = await api.get(`/attachments/${attachmentId}`);
        return data;
    },

    // Download attachment
    download: async (attachmentId: string): Promise<Blob> => {
        const response = await api.get(`/attachments/${attachmentId}/download`, {
            responseType: "blob",
        });
        return response.data;
    },

    // Delete attachment
    delete: async (attachmentId: string): Promise<void> => {
        await api.delete(`/attachments/${attachmentId}`);
    },

    // List attachments
    list: async (resourceType?: string, resourceId?: string) => {
        const params = new URLSearchParams();
        if (resourceType) params.append("resource_type", resourceType);
        if (resourceId) params.append("resource_id", resourceId);
        const query = params.toString();
        const { data } = await api.get(`/attachments${query ? `?${query}` : ""}`);
        return data;
    },
};

