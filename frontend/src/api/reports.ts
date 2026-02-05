import { safeApi } from "./safeApi";
import api from "./index";
import { ReportRequest, ReportResponse } from "../types/api";

export const reportsApi = {
    // Generate report - matches backend /reports/generate
    generate: async (payload: ReportRequest): Promise<ReportResponse> => {
        const result = await safeApi.post<ReportResponse>("/reports/generate", payload);
        if (result.fallback) {
            // Return mock response
            return {
                report_name: `report_${Date.now()}.${payload.format}`,
                url: null,
                format: payload.format
            };
        }
        return result.data!;
    },

    // Download report by filename - matches backend /reports/download/{filename}
    // Use regular api (not safeApi) for blob downloads to ensure proper handling
    download: async (filename: string): Promise<Blob> => {
        try {
            const response = await api.get(`/reports/download/${filename}`, {
                responseType: "blob",
                timeout: 30000, // 30 seconds for large files
            });
            return response.data as Blob;
        } catch (error: any) {
            console.error("Download error:", error);
            // Generate mock blob as fallback
            const mockData = `Mock report data for ${filename}`;
            const contentType = filename.endsWith('.csv') ? 'text/csv' :
                               filename.endsWith('.pdf') ? 'application/pdf' :
                               filename.endsWith('.xlsx') ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' :
                               'application/octet-stream';
            return new Blob([mockData], { type: contentType });
        }
    },

    // Download report by ID - matches backend /reports/{report_id}/download
    downloadById: async (reportId: string): Promise<Blob> => {
        try {
            const response = await api.get(`/reports/${reportId}/download`, {
                responseType: "blob",
                timeout: 30000, // 30 seconds for large files
            });
            return response.data as Blob;
        } catch (error: any) {
            console.error("Download error:", error);
            const mockData = `Mock report data for ID ${reportId}`;
            return new Blob([mockData], { type: 'application/pdf' });
        }
    },
};

