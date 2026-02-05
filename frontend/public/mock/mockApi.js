// Complete Mock API System - Works Offline
// All data stored in memory

const mockData = {
    users: [
        { id: '1', email: 'admin@example.com', name: 'Admin User', role: 'admin' },
        { id: '2', email: 'engineer@example.com', name: 'Engineer', role: 'engineer' },
        { id: '3', email: 'viewer@example.com', name: 'Viewer', role: 'viewer' }
    ],
    machines: [
        { id: '1', name: 'Motor-01', type: 'Motor', location: 'Floor A', status: 'active', health_score: 85 },
        { id: '2', name: 'Compressor-A', type: 'Compressor', location: 'Floor B', status: 'active', health_score: 72 },
        { id: '3', name: 'Pump-01', type: 'Pump', location: 'Floor C', status: 'active', health_score: 90 }
    ],
    sensors: [
        { id: '1', machine_id: '1', name: 'Temperature', type: 'temperature', value: 75.5, unit: '°C', status: 'normal' },
        { id: '2', machine_id: '1', name: 'Vibration', type: 'vibration', value: 3.2, unit: 'mm/s', status: 'normal' },
        { id: '3', machine_id: '2', name: 'Pressure', type: 'pressure', value: 150.0, unit: 'psi', status: 'warning' }
    ],
    predictions: [],
    alarms: [],
    tickets: [],
    reports: [],
    settings: [],
    webhooks: [],
    roles: [
        { id: '1', name: 'Admin', permissions: ['all'] },
        { id: '2', name: 'Engineer', permissions: ['machines', 'sensors', 'predictions'] },
        { id: '3', name: 'Viewer', permissions: ['read'] }
    ],
    auditLogs: []
};

// Generate initial mock data
function initMockData() {
    const now = new Date();
    for (let i = 0; i < 50; i++) {
        mockData.predictions.push({
            id: `pred-${i}`,
            machine_id: mockData.machines[Math.floor(Math.random() * mockData.machines.length)].id,
            sensor_id: mockData.sensors[Math.floor(Math.random() * mockData.sensors.length)].id,
            timestamp: new Date(now - i * 60000).toISOString(),
            score: Math.random(),
            confidence: 0.7 + Math.random() * 0.2,
            status: ['normal', 'warning', 'critical'][Math.floor(Math.random() * 3)],
            prediction: Math.random() > 0.7 ? 'anomaly' : 'normal'
        });
    }
    
    for (let i = 0; i < 20; i++) {
        mockData.alarms.push({
            id: `alarm-${i}`,
            machine_id: mockData.machines[Math.floor(Math.random() * mockData.machines.length)].id,
            sensor_id: mockData.sensors[Math.floor(Math.random() * mockData.sensors.length)].id,
            severity: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)],
            status: ['active', 'resolved'][Math.floor(Math.random() * 2)],
            message: `Alarm ${i + 1}: Sensor reading exceeded threshold`,
            timestamp: new Date(now - i * 3600000).toISOString()
        });
    }
}
initMockData();

// Mock API Functions
const mockApi = {
    // Authentication
    login: (email, password) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const user = mockData.users.find(u => u.email === email);
                if (user && password === 'password123') {
                    localStorage.setItem('mock_token', 'mock-jwt-token');
                    localStorage.setItem('mock_user', JSON.stringify(user));
                    resolve({ access_token: 'mock-jwt-token', user });
                } else {
                    resolve({ error: 'Invalid credentials' });
                }
            }, 500);
        });
    },
    
    logout: () => {
        localStorage.removeItem('mock_token');
        localStorage.removeItem('mock_user');
    },
    
    getCurrentUser: () => {
        const user = localStorage.getItem('mock_user');
        return user ? JSON.parse(user) : null;
    },
    
    // Machines
    getMachines: () => Promise.resolve(mockData.machines),
    getMachine: (id) => Promise.resolve(mockData.machines.find(m => m.id === id)),
    createMachine: (data) => {
        const machine = { id: String(mockData.machines.length + 1), ...data, created_at: new Date().toISOString() };
        mockData.machines.push(machine);
        return Promise.resolve(machine);
    },
    updateMachine: (id, data) => {
        const index = mockData.machines.findIndex(m => m.id === id);
        if (index !== -1) {
            mockData.machines[index] = { ...mockData.machines[index], ...data };
            return Promise.resolve(mockData.machines[index]);
        }
        return Promise.reject('Machine not found');
    },
    deleteMachine: (id) => {
        mockData.machines = mockData.machines.filter(m => m.id !== id);
        return Promise.resolve();
    },
    
    // Sensors
    getSensors: (machineId) => {
        let sensors = mockData.sensors;
        if (machineId) sensors = sensors.filter(s => s.machine_id === machineId);
        return Promise.resolve(sensors);
    },
    getSensor: (id) => Promise.resolve(mockData.sensors.find(s => s.id === id)),
    createSensor: (data) => {
        const sensor = { id: String(mockData.sensors.length + 1), ...data, created_at: new Date().toISOString() };
        mockData.sensors.push(sensor);
        return Promise.resolve(sensor);
    },
    updateSensor: (id, data) => {
        const index = mockData.sensors.findIndex(s => s.id === id);
        if (index !== -1) {
            mockData.sensors[index] = { ...mockData.sensors[index], ...data };
            return Promise.resolve(mockData.sensors[index]);
        }
        return Promise.reject('Sensor not found');
    },
    deleteSensor: (id) => {
        mockData.sensors = mockData.sensors.filter(s => s.id !== id);
        return Promise.resolve();
    },
    
    // Predictions
    getPredictions: (limit = 50) => Promise.resolve(mockData.predictions.slice(0, limit)),
    getPrediction: (id) => Promise.resolve(mockData.predictions.find(p => p.id === id)),
    triggerPrediction: (machineId, sensorId) => {
        const prediction = {
            id: `pred-${Date.now()}`,
            machine_id: machineId,
            sensor_id: sensorId,
            timestamp: new Date().toISOString(),
            score: Math.random(),
            confidence: 0.7 + Math.random() * 0.2,
            status: Math.random() > 0.7 ? 'warning' : 'normal',
            prediction: Math.random() > 0.8 ? 'anomaly' : 'normal'
        };
        mockData.predictions.unshift(prediction);
        return Promise.resolve(prediction);
    },
    
    // Alarms
    getAlarms: () => Promise.resolve(mockData.alarms),
    getAlarm: (id) => Promise.resolve(mockData.alarms.find(a => a.id === id)),
    resolveAlarm: (id) => {
        const alarm = mockData.alarms.find(a => a.id === id);
        if (alarm) alarm.status = 'resolved';
        return Promise.resolve(alarm);
    },
    
    // Tickets
    getTickets: () => Promise.resolve(mockData.tickets),
    createTicket: (data) => {
        const ticket = { id: `ticket-${Date.now()}`, ...data, status: 'open', created_at: new Date().toISOString() };
        mockData.tickets.push(ticket);
        return Promise.resolve(ticket);
    },
    
    // Reports
    generateReport: (format, dateFrom, dateTo, machineId) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                let blob;
                let filename;
                const data = 'Mock report data\nMachine: ' + (machineId || 'All') + '\nDate: ' + dateFrom + ' to ' + dateTo;
                
                if (format === 'csv') {
                    blob = new Blob([data], { type: 'text/csv' });
                    filename = `report_${Date.now()}.csv`;
                } else if (format === 'pdf') {
                    // Mock PDF - create a simple text file
                    blob = new Blob([data], { type: 'application/pdf' });
                    filename = `report_${Date.now()}.pdf`;
                } else if (format === 'xlsx') {
                    blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                    filename = `report_${Date.now()}.xlsx`;
                }
                
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                link.click();
                URL.revokeObjectURL(url);
                
                resolve({ success: true, filename });
            }, 1000);
        });
    },
    
    // Simulator
    triggerSimulation: (type, params) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                // Generate mock simulation data
                const result = {
                    success: true,
                    message: `Simulation ${type} triggered`,
                    data: { ...params, timestamp: new Date().toISOString() }
                };
                resolve(result);
            }, 500);
        });
    },
    
    // Dashboard
    getDashboard: () => Promise.resolve({
        machines: { total: mockData.machines.length, online: mockData.machines.filter(m => m.status === 'active').length },
        sensors: { total: mockData.sensors.length },
        alarms: { active: mockData.alarms.filter(a => a.status === 'active').length },
        predictions: { last_24h: mockData.predictions.length }
    }),
    
    // AI Service
    getAIStatus: () => Promise.resolve({ status: 'healthy', model_loaded: true, version: '1.0.0' }),
    retrainAI: () => {
        return new Promise((resolve) => {
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                if (progress >= 100) {
                    clearInterval(interval);
                    resolve({ success: true, message: 'Retraining complete' });
                }
            }, 500);
        });
    },
    
    // MQTT Status
    getMQTTStatus: () => Promise.resolve({ connected: true, last_message: new Date().toISOString() }),
    
    // OPC UA
    getOPCUAStatus: () => Promise.resolve({ connected: false, sources: [] }),
    
    // Settings
    getSettings: () => Promise.resolve(mockData.settings),
    updateSetting: (key, value) => {
        const setting = mockData.settings.find(s => s.key === key);
        if (setting) {
            setting.value = value;
        } else {
            mockData.settings.push({ key, value });
        }
        return Promise.resolve({ key, value });
    },
    
    // Webhooks
    getWebhooks: () => Promise.resolve(mockData.webhooks),
    createWebhook: (data) => {
        const webhook = { id: `webhook-${Date.now()}`, ...data, enabled: true };
        mockData.webhooks.push(webhook);
        return Promise.resolve(webhook);
    },
    
    // Roles
    getRoles: () => Promise.resolve(mockData.roles),
    createRole: (data) => {
        const role = { id: String(mockData.roles.length + 1), ...data };
        mockData.roles.push(role);
        return Promise.resolve(role);
    },
    
    // Audit Logs
    getAuditLogs: (filters) => Promise.resolve(mockData.auditLogs)
};

// SSE Simulator
function simulateSSE(callback) {
    const events = ['new_sensor_data', 'new_prediction', 'new_alarm', 'ai_retrain_complete', 'opcua_test_result', 'mqtt_status_change'];
    
    setInterval(() => {
        const event = events[Math.floor(Math.random() * events.length)];
        const data = {
            type: event,
            timestamp: new Date().toISOString(),
            data: generateEventData(event)
        };
        callback(data);
    }, 5000);
}

function generateEventData(eventType) {
    switch (eventType) {
        case 'new_sensor_data':
            return {
                sensor_id: mockData.sensors[Math.floor(Math.random() * mockData.sensors.length)].id,
                value: Math.random() * 100,
                timestamp: new Date().toISOString()
            };
        case 'new_prediction':
            return mockData.predictions[0] || {};
        case 'new_alarm':
            return {
                id: `alarm-${Date.now()}`,
                severity: 'warning',
                message: 'New alarm triggered',
                timestamp: new Date().toISOString()
            };
        default:
            return { message: 'Event triggered' };
    }
}

// Export for use
if (typeof window !== 'undefined') {
    window.mockApi = mockApi;
    window.simulateSSE = simulateSSE;
}

