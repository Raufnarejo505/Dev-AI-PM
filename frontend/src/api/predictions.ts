import { safeApi } from "./safeApi";

export interface Prediction {
  id: string;
  machine_id: string;
  sensor_id: string;
  timestamp: string;
  score: number;
  confidence: number;
  status: 'normal' | 'warning' | 'critical';
  prediction: 'normal' | 'anomaly';
  anomaly_type?: string;
}

export const predictionsApi = {
  // Get recent predictions - real-time data
  getRecent: async (limit: number = 30): Promise<Prediction[]> => {
    const result = await safeApi.get<Prediction[]>(`/predictions?limit=${limit}&sort=desc`);
    if (result.fallback) {
      // Return static mock data when offline
      const now = new Date();
      return Array.from({ length: limit }, (_, i) => ({
        id: `mock-pred-${i}`,
        machine_id: 'mock-machine',
        sensor_id: 'mock-sensor',
        timestamp: new Date(now.getTime() - i * 60000).toISOString(),
        score: 0.5 + Math.random() * 0.3,
        confidence: 0.7 + Math.random() * 0.2,
        status: i % 3 === 0 ? 'critical' : i % 3 === 1 ? 'warning' : 'normal',
        prediction: i % 3 === 0 ? 'anomaly' : 'normal',
      }));
    }
    return result.data || [];
  },
  
  // Get predictions for a specific machine
  getByMachine: async (machineId: string, limit: number = 50): Promise<Prediction[]> => {
    const result = await safeApi.get<Prediction[]>(`/predictions?machine_id=${machineId}&limit=${limit}`);
    return result.data || [];
  },
  
  // Get predictions for a specific sensor
  getBySensor: async (sensorId: string, limit: number = 50): Promise<Prediction[]> => {
    const result = await safeApi.get<Prediction[]>(`/predictions?sensor_id=${sensorId}&limit=${limit}`);
    return result.data || [];
  },
  
  // Trigger manual prediction
  trigger: async (machineId: string, sensorId?: string): Promise<Prediction> => {
    const result = await safeApi.post<Prediction>('/predictions/trigger', {
      machine_id: machineId,
      sensor_id: sensorId,
    });
    if (result.fallback) {
      throw new Error('Backend offline - cannot trigger prediction');
    }
    return result.data!;
  },
};
