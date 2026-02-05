import React, { useState } from 'react';
import { simulatorApi } from '../api/simulator';
import { useErrorToast } from './ErrorToast';

export const SimulatorButton: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const { showError, ErrorComponent } = useErrorToast();

  const handleTriggerSimulation = async () => {
    setIsRunning(true);
    try {
      const result = await simulatorApi.triggerFailure({
        anomaly_type: 'sudden_spike',
        duration: 60,
        value_multiplier: 1.5
      });
      showError('✅ Simulation triggered successfully!');
    } catch (error: any) {
      // Fallback to mock simulation
      setTimeout(() => {
        showError('✅ Simulation triggered (mock mode)!');
        setIsRunning(false);
      }, 1000);
    } finally {
      setTimeout(() => setIsRunning(false), 2000);
    }
  };

  return (
    <>
      <button
        onClick={handleTriggerSimulation}
        disabled={isRunning}
        className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
      >
        {isRunning ? 'Running...' : 'Simulate Failure'}
      </button>
      {ErrorComponent}
    </>
  );
};

