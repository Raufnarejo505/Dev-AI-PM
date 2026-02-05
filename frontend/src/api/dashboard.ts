/**
 * Dashboard API - Enhanced with live data generation fallback
 */
import api from "./index";
import { DashboardOverview } from "../types/api";

export const dashboardApi = {
    /**
     * Get dashboard overview with live data
     */
    async getOverview(): Promise<DashboardOverview> {
        const response = await api.get<DashboardOverview>("/dashboard/overview");
        return response.data;
    },

    /**
     * Generate test data if no live data available
     */
    async generateTestData(count: number = 10): Promise<{ ok: boolean; message: string }> {
        const response = await api.post("/simulator/generate-test-data", null, {
            params: { count },
        });
        return response.data;
    },

    /**
     * Get machine summary with live data
     */
    async getMachineSummary(machineId: string): Promise<any> {
        const response = await api.get<any>(`/machines/${machineId}/summary`);
        return response.data;
    },

    /**
     * Get MSSQL extruder latest rows
     */
    async getExtruderLatest(): Promise<{ rows: any[] }> {
        const response = await api.get<{ rows: any[] }>("/dashboard/extruder/latest");
        return response.data;
    },

    /**
     * Get MSSQL extruder connection status
     */
    async getExtruderStatus(): Promise<any> {
        const response = await api.get<any>("/dashboard/extruder/status");
        return response.data;
    },

    /**
     * Get MSSQL extruder derived KPIs, baseline, and risk indicators
     */
    async getExtruderDerived(windowMinutes: number = 30): Promise<any> {
        const response = await api.get<any>("/dashboard/extruder/derived", {
            params: { window_minutes: windowMinutes },
        });
        return response.data;
    },
};
