import { create } from 'zustand';
import { API_BASE_URL } from '../api/index'; // Import API_BASE_URL for consistency

interface BackendState {
  status: 'online' | 'offline' | 'checking';
  lastCheck: Date | null;
  healthCheckInterval: NodeJS.Timeout | null;
  setStatus: (status: 'online' | 'offline' | 'checking') => void;
  setLastCheck: (date: Date) => void;
  startHealthCheck: () => void;
  stopHealthCheck: () => void;
}

export const useBackendStore = create<BackendState>((set) => ({
  status: 'checking',
  lastCheck: null,
  healthCheckInterval: null,
  
  setStatus: (status) => set({ status }),
  setLastCheck: (date) => set({ lastCheck: date }),
  
  startHealthCheck: () => {
    const checkHealth = async () => {
      try {
        // Use the imported API_BASE_URL for consistency
        const response = await fetch(`${API_BASE_URL}/health/live`, {
          method: 'GET',
          signal: AbortSignal.timeout(5000), // Increased timeout to 5 seconds
        });
        
        if (response.ok) {
          set({ status: 'online', lastCheck: new Date() });
        } else {
          set({ status: 'offline', lastCheck: new Date() });
        }
      } catch (error) {
        set({ status: 'offline', lastCheck: new Date() });
      }
    };
    
    // Initial check
    checkHealth();
    
    // Check every 5 seconds
    const interval = setInterval(checkHealth, 5000);
    set({ healthCheckInterval: interval });
  },
  
  stopHealthCheck: () => {
    const state = useBackendStore.getState();
    if (state.healthCheckInterval) {
      clearInterval(state.healthCheckInterval);
      set({ healthCheckInterval: null });
    }
  },
}));

