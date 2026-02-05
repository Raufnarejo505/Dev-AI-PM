import React, { useState, useEffect, useMemo } from 'react';
import { useBackendStore } from '../store/backendStore';
import { safeApi } from '../api/safeApi';
import { StatusBadge } from '../components/StatusBadge';
import { formatDateTime, formatPercentage } from '../utils/formatters';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { ChartSkeleton, ListSkeleton } from '../components/FallbackSkeleton';
import { BackendStatusBanner } from '../components/BackendStatusBanner';

interface Prediction {
  id: string;
  machine_id: string;
  sensor_id: string;
  timestamp: string;
  score: number;
  confidence: number;
  status: string;
  prediction: string;
}

export default function PredictionsPage() {
  const [selectedMachine, setSelectedMachine] = useState<string>('all');
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [machines, setMachines] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFallback, setIsFallback] = useState(false);
  
  const backendStatus = useBackendStore((state) => state.status);
  
  // Fetch predictions - optimized to prevent freezing
  useEffect(() => {
    let mounted = true;
    let timeoutId: NodeJS.Timeout;
    
    const fetchData = async () => {
      setIsLoading(true);
      
      try {
        // Fetch predictions with limit to prevent overload
        const predResult = await safeApi.get<Prediction[]>('/predictions?limit=50&sort=desc');
        
        if (!mounted) return;
        
        if (predResult.fallback) {
          setIsFallback(true);
          setPredictions(Array.isArray(predResult.data) ? predResult.data : []);
        } else {
          setIsFallback(false);
          setPredictions(Array.isArray(predResult.data) ? predResult.data : []);
        }
        
        // Fetch machines
        const machinesResult = await safeApi.get<any[]>('/machines');
        if (mounted && machinesResult.data) {
          setMachines(Array.isArray(machinesResult.data) ? machinesResult.data : []);
        }
      } catch (error) {
        console.error('Error fetching predictions:', error);
        setIsFallback(true);
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };
    
    fetchData();
    
    // Refresh every 10 seconds (reduced from 8s to prevent overload)
    const interval = setInterval(() => {
      if (backendStatus === 'online') {
        fetchData();
      }
    }, 10000);
    
    return () => {
      mounted = false;
      clearInterval(interval);
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [backendStatus]);
  
  // Memoize filtered predictions to prevent unnecessary recalculations
  const filteredPredictions = useMemo(() => {
    if (selectedMachine === 'all') return predictions;
    return predictions.filter((p) => p.machine_id === selectedMachine);
  }, [predictions, selectedMachine]);
  
  // Memoize chart data
  const chartData = useMemo(() => {
    return filteredPredictions.slice(-30).map((p) => ({
      timestamp: new Date(p.timestamp).toLocaleTimeString(),
      score: p.confidence || p.score || 0,
      status: p.status,
    }));
  }, [filteredPredictions]);
  
  return (
    <div className="space-y-6">
      <BackendStatusBanner />
      
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">AI Predictions</h1>
          <p className="text-slate-400 mt-1">
            {isFallback ? 'Showing fallback data - Backend offline' : 'View and analyze AI predictions'}
          </p>
        </div>
        <select
          value={selectedMachine}
          onChange={(e) => setSelectedMachine(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
          disabled={isFallback}
        >
          <option value="all">All Machines</option>
          {machines.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
      </div>
      
      {/* Prediction Trends Chart */}
      <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Prediction Trends</h2>
        {isLoading ? (
          <ChartSkeleton />
        ) : chartData.length > 0 ? (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis 
                  dataKey="timestamp" 
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  domain={[0, 1]} 
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #475569',
                    borderRadius: '8px'
                  }}
                />
                <ReferenceLine y={0.8} stroke="#ef4444" strokeDasharray="5 5" />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#22d3ee" 
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-slate-400">
            {isFallback ? 'No data available (Backend offline)' : 'No prediction data available'}
          </div>
        )}
      </div>
      
      {/* Recent Predictions */}
      <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Recent Predictions</h2>
        {isLoading ? (
          <ListSkeleton count={10} />
        ) : filteredPredictions.length > 0 ? (
          <div className="space-y-3">
            {filteredPredictions.slice(0, 20).map((prediction) => (
              <div
                key={prediction.id}
                className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-lg hover:border-emerald-500/40 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-100">
                        Confidence: {formatPercentage(prediction.confidence || prediction.score || 0)}
                      </span>
                      <StatusBadge status={prediction.status || 'normal'} />
                      {isFallback && (
                        <span className="text-xs text-amber-400/80">(Fallback)</span>
                      )}
                    </div>
                    <p className="text-sm text-slate-400 mt-1">
                      {formatDateTime(prediction.timestamp)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">
            {isFallback ? 'No data available (Backend offline)' : 'No predictions found'}
          </div>
        )}
      </div>
    </div>
  );
}
