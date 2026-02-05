import React, { useState, useEffect } from 'react';
import { safeApi } from '../api/safeApi';
import { useT } from '../i18n/I18nProvider';

interface LiveDataRow {
  timestamp: string;
  temperature: number;
  vibration: number;
  anomaly: number;
  prediction: string;
  machine?: string;
}

export const LiveDataTable: React.FC = () => {
  const t = useT();
  const [data, setData] = useState<LiveDataRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFallback, setIsFallback] = useState(false);

  useEffect(() => {
    const fetchLiveData = async () => {
      try {
        // Fetch recent sensor data and predictions
        const [sensorDataResult, predictionsResult] = await Promise.all([
          safeApi.get('/sensor-data/logs?limit=20&sort=desc'),
          safeApi.get('/predictions?limit=20&sort=desc'),
        ]);

        if (sensorDataResult.fallback || predictionsResult.fallback) {
          setIsFallback(true);
          return;
        }

        setIsFallback(false);

        // Combine sensor data with predictions
        const sensorData = sensorDataResult.data || [];
        const predictions = predictionsResult.data || [];

        // Group sensor data by timestamp and extract values by sensor type/category
        const sensorMap = new Map<string, any>();
        sensorData.forEach((sensor: any) => {
          const key = sensor.timestamp || sensor.created_at;
          if (!sensorMap.has(key)) {
            sensorMap.set(key, {
              timestamp: new Date(sensor.timestamp || sensor.created_at),
              sensors: {},
              machine: sensor.machine?.name || sensor.machine_id || 'Unknown',
              prediction: null,
            });
          }
          const entry = sensorMap.get(key);
          const sensorName = sensor.sensor?.name || sensor.sensor_id || 'Unknown';
          // Try multiple ways to get sensor type/category
          const sensorType = sensor.sensor?.sensor_type || 
                            sensor.metadata?.category || 
                            sensor.metadata?.alias?.toLowerCase() ||
                            sensorName.toLowerCase().replace(/\s+/g, '_');
          
          // Map common OPC UA aliases to standard types
          const typeMap: Record<string, string> = {
            'opcua_temperature': 'temperature',
            'opcua_vibration': 'vibration',
            'opcua_motor_current': 'motor_current',
            'opcua_pressure': 'pressure',
            'opcua_wear_index': 'wear',
            'temperature': 'temperature',
            'vibration': 'vibration',
            'pressure': 'pressure',
            'motor_current': 'motor_current',
          };
          
          const normalizedType = typeMap[sensorType] || sensorType;
          entry.sensors[normalizedType] = {
            value: parseFloat(sensor.value) || 0,
            unit: sensor.sensor?.unit || sensor.metadata?.unit || '',
            name: sensorName,
          };
        });

        // Match predictions with sensor data by timestamp (within 5 seconds)
        predictions.forEach((pred: any) => {
          const predTime = new Date(pred.timestamp || pred.created_at).getTime();
          for (const [key, entry] of sensorMap.entries()) {
            const entryTime = entry.timestamp.getTime();
            if (Math.abs(predTime - entryTime) < 5000) { // Within 5 seconds
              entry.prediction = pred;
              break;
            }
          }
        });

        // Convert to table format, showing latest readings
        const tableData: LiveDataRow[] = Array.from(sensorMap.values())
          .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
          .slice(0, 10)
          .map((entry) => {
            const pred = entry.prediction || {};
            return {
              timestamp: entry.timestamp.toLocaleTimeString('de-DE', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              }),
              temperature: entry.sensors.temperature?.value || 0,
              vibration: entry.sensors.vibration?.value || 0,
              anomaly: pred.score || pred.confidence || 0,
              prediction: pred.prediction === 'anomaly' ? t('liveData.predictionAnomaly') : 
                         pred.status === 'warning' ? t('liveData.predictionWarning') : 
                         pred.status === 'critical' ? t('liveData.predictionCritical') : t('liveData.predictionHealthy'),
              machine: entry.machine,
            };
          });

        setData(tableData);
      } catch (error) {
        console.error('Error fetching live data:', error);
        setIsFallback(true);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLiveData();
    // Update every 2 seconds to match OPC UA polling frequency (typically 1-2 seconds)
    const interval = setInterval(fetchLiveData, 2000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">{t('liveData.title')}</h2>
        <div className="text-slate-400 text-sm">{t('common.loading')}</div>
      </div>
    );
  }

  if (isFallback) {
    return (
      <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">{t('liveData.title')}</h2>
        <div className="text-slate-400 text-sm">{t('liveData.noLiveDataOffline')}</div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-6">
      <h2 className="text-lg font-semibold text-slate-100 mb-4">{t('liveData.title')}</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="text-left py-2 px-3 text-slate-400 font-medium">{t('liveData.timestamp')}</th>
              <th className="text-left py-2 px-3 text-slate-400 font-medium">{t('liveData.temperature')}</th>
              <th className="text-left py-2 px-3 text-slate-400 font-medium">{t('liveData.vibration')}</th>
              <th className="text-left py-2 px-3 text-slate-400 font-medium">{t('liveData.anomaly')}</th>
              <th className="text-left py-2 px-3 text-slate-400 font-medium">{t('liveData.prediction')}</th>
            </tr>
          </thead>
          <tbody>
            {data.length > 0 ? (
              data.map((row, idx) => (
                <tr
                  key={idx}
                  className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                >
                  <td className="py-2 px-3 text-slate-300 font-mono text-xs">{row.timestamp}</td>
                  <td className="py-2 px-3 text-slate-200">{row.temperature.toFixed(1)}°C</td>
                  <td className="py-2 px-3 text-slate-200">{row.vibration.toFixed(2)}g</td>
                  <td className="py-2 px-3 text-slate-200">{row.anomaly.toFixed(2)}</td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      row.prediction.includes('Anomaly') ? 'bg-red-500/20 text-red-300' :
                      row.prediction.includes('Warning') ? 'bg-yellow-500/20 text-yellow-300' :
                      'bg-green-500/20 text-green-300'
                    }`}>
                      {row.prediction}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="py-4 text-center text-slate-400">
                  {t('liveData.noData')}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

