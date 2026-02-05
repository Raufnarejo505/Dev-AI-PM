import { safeApi } from "./safeApi";

export const simulatorApi = {
    // Trigger failure simulation - matches backend /simulator/trigger-failure
    triggerFailure: async (payload: {
        machine_id?: string;
        sensor_id?: string;
        anomaly_type?: string;
        duration?: number;
        value_multiplier?: number;
    }) => {
        const result = await safeApi.post("/simulator/trigger-failure", payload);
        if (result.fallback) {
            // Mock simulation when backend offline
            return {
                ok: true,
                message: `Simulated ${payload.anomaly_type || 'critical'} anomaly (mock mode)`,
                machine_id: payload.machine_id || "machine-1",
                sensor_id: payload.sensor_id || "pressure-head",
                readings_sent: payload.duration ? Math.min(Math.floor(payload.duration / 2), 30) : 30
            };
        }
        return result.data;
    },
    
    // Generate test data - matches backend /simulator/generate-test-data
    generateTestData: async (count: number = 10) => {
        const result = await safeApi.post("/simulator/generate-test-data", null, {
            params: { count }
        });
        if (result.fallback) {
            return {
                ok: true,
                message: `Generated ${count} batches of test data (mock mode)`,
                records_created: count * 10
            };
        }
        return result.data;
    },
};

