# Machine State Detection System

## Overview

The Machine State Detection System provides intelligent, real-time detection of machine operating states with **process evaluation (traffic-light rating, baseline comparison, anomaly detection) enabled ONLY in PRODUCTION state**. All other phases (OFF, HEATING, IDLE, COOLING) show status only without process evaluation.

## 🎯 Core Principle

**Process evaluation runs exclusively in PRODUCTION state** - this prevents false alarms during startup, shutdown, and standby phases while ensuring comprehensive monitoring during actual production.

## 🗂️ Machine States

### 1. OFF
- **Description**: Machine off / cold
- **Entry Criteria**:
  - `screw_rpm < RPM_ON` AND
  - `pressure_bar < P_ON` AND  
  - `temp_avg < T_MIN_ACTIVE`
- **UI Display**: "Machine OFF / cold"
- **Traffic Light**: Neutral/gray
- **Process Evaluation**: ❌ Disabled

### 2. HEATING  
- **Description**: Warming up, not producing
- **Entry Criteria**:
  - `temp_avg ≥ T_MIN_ACTIVE` AND
  - `d_temp_avg ≥ HEATING_RATE` AND
  - `screw_rpm < RPM_PROD`
- **UI Display**: "Heating – no process evaluation yet"
- **Traffic Light**: Blue/gray
- **Process Evaluation**: ❌ Disabled

### 3. IDLE
- **Description**: Warm and ready, but not producing
- **Entry Criteria**:
  - `temp_avg ≥ T_MIN_ACTIVE` AND
  - `abs(d_temp_avg) < 0.2 °C/min` (flat) AND
  - `screw_rpm < RPM_ON` AND
  - `pressure_bar < P_ON`
- **UI Display**: "Ready/Standby – no production"
- **Traffic Light**: Neutral/gray
- **Process Evaluation**: ❌ Disabled

### 4. PRODUCTION ⭐
- **Description**: Active process - **ONLY state with process evaluation**
- **Primary Entry Criteria**:
  - `screw_rpm ≥ RPM_PROD` AND `pressure_bar ≥ P_PROD`
  - **Stable for ≥ 90 seconds**
- **Fallback Entry Criteria**:
  - `screw_rpm ≥ RPM_PROD` AND (`pressure_bar ≥ P_ON` OR `motor_load ≥ 15%` OR `throughput > 0`)
  - **Stable for ≥ 90 seconds**
- **UI Display**: "Production"
- **Traffic Light**: ✅ **ENABLED** (Green/Yellow/Red)
- **Process Evaluation**: ✅ **ENABLED** (Traffic light + baseline + anomalies)

### 5. COOLING
- **Description**: Cooling down, not producing
- **Entry Criteria**:
  - `screw_rpm < RPM_ON` AND
  - `d_temp_avg ≤ COOLING_RATE`
- **UI Display**: "Cooling – no process evaluation"
- **Traffic Light**: Neutral/gray
- **Process Evaluation**: ❌ Disabled

### 6. UNKNOWN / SENSOR_FAULT
- **Description**: Sensor error or invalid data
- **Entry Criteria**: Sensor validation failures
- **UI Display**: "Sensor error – no evaluation"
- **Traffic Light**: Neutral/gray
- **Process Evaluation**: ❌ Disabled

## 📊 Derived Metrics

The system calculates these metrics for state detection:

### Core Metrics
- **`temp_avg`**: Mean of available temperature zones
- **`temp_spread`**: `max(zones) - min(zones)`
- **`d_temp_avg`**: Temperature slope in °C/min (5-minute window)
- **`rpm_stable`**: Standard deviation of RPM over 60 seconds
- **`pressure_stable`**: Standard deviation of pressure over 60 seconds

### Convenience Flags
- **`any_temp_above_min`**: Any zone > T_MIN_ACTIVE
- **`all_temps_below`**: All zones < T_MIN_ACTIVE

## 🔧 Default Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `RPM_ON` | 5.0 rpm | Movement present |
| `RPM_PROD` | 10.0 rpm | Production possible |
| `P_ON` | 2.0 bar | Pressure present |
| `P_PROD` | 5.0 bar | Typical production pressure |
| `T_MIN_ACTIVE` | 60.0 °C | Below this = cold/off |
| `HEATING_RATE` | +0.2 °C/min | Positive heating |
| `COOLING_RATE` | -0.2 °C/min | Negative cooling |
| `MOTOR_LOAD_MIN` | 15% | Production fallback |
| `THROUGHPUT_MIN` | 0.1 kg/h | Production fallback |

## ⏱️ Hysteresis & Debounce

### State Transition Timers
- **Enter PRODUCTION**: 90 seconds sustained criteria
- **Exit PRODUCTION**: 120 seconds sustained non-production
- **Other state changes**: 60 seconds debounce

### Purpose
- Prevent rapid state oscillation
- Ensure stable production detection
- Reduce false alarms during transitions

## 🚨 Sensor Fault Detection

### Fault Conditions
- Temperature ≤ 0°C or < -20°C (implausible)
- Temperature > 400°C (unlikely for extruder)
- Pressure = 0 while RPM > RPM_PROD
- Missing critical data (RPM, insufficient temp zones)
- Invalid timestamps

### Response
- Set state: `UNKNOWN / SENSOR_FAULT`
- UI: "Sensor error – no evaluation"
- Alert: "Please check sensor"

## 🔄 State Transitions

```
OFF → HEATING: temp ≥ T_MIN_ACTIVE and dT > 0
HEATING → PRODUCTION: production criteria ≥ 90s
HEATING → IDLE: warm, no RPM/pressure, flat gradient
IDLE → PRODUCTION: production criteria ≥ 90s
PRODUCTION → IDLE: RPM < RPM_ON and pressure < P_ON ≥ 120s
PRODUCTION → COOLING: RPM off and temperature falling
COOLING → OFF: temp < T_MIN_ACTIVE and no RPM/pressure
COOLING → HEATING: gradient turns positive
Any → SENSOR_FAULT: critical data invalid
```

## 🏗️ Architecture

### Components
1. **MachineStateDetector**: Core detection engine
2. **MachineStateService**: Database operations and business logic
3. **MQTT Integration**: Real-time sensor data processing
4. **API Layer**: Configuration and monitoring endpoints
5. **Database Models**: State history, thresholds, alerts

### Data Flow
```
Sensor Data → MQTT Consumer → State Detection → Database → UI Updates
                                      ↓
                              Process Evaluation (PRODUCTION only)
                                      ↓
                              Traffic Light + Baseline + Anomalies
```

## 📡 API Endpoints

### State Management
- `GET /api/machine-state/states/current` - All machine states
- `GET /api/machine-state/states/{machine_id}/current` - Specific machine state
- `GET /api/machine-state/states/{machine_id}/history` - State transition history
- `GET /api/machine-state/states/{machine_id}/statistics` - State statistics

### Configuration
- `GET /api/machine-state/thresholds/{machine_id}` - Get thresholds
- `POST /api/machine-state/thresholds/{machine_id}` - Create/update thresholds
- `PUT /api/machine-state/thresholds/{machine_id}` - Update thresholds
- `DELETE /api/machine-state/thresholds/{machine_id}` - Delete thresholds

### Process Evaluation
- `POST /api/machine-state/evaluate/{machine_id}` - Trigger evaluation
- `GET /api/machine-state/evaluations/{machine_id}` - Evaluation history

### Alerts
- `GET /api/machine-state/alerts/{machine_id}` - State alerts

## 🎨 Frontend Integration

### State Display
- **Status Banner**: Shows current state prominently
- **State Color Coding**:
  - OFF: Gray
  - HEATING: Blue
  - IDLE: Yellow
  - PRODUCTION: Green
  - COOLING: Orange
  - SENSOR_FAULT: Red

### Traffic Light (PRODUCTION only)
- **Green**: Normal operation
- **Yellow**: Warning/attention needed
- **Red**: Critical action required
- **Hidden**: All other states

### Real-time Updates
- WebSocket updates for state changes
- Auto-refresh dashboard every 10 seconds
- Process evaluation results broadcast immediately

## 🧪 Testing

### Test Scenarios
1. **OFF**: `rpm=0, p=0, temp=25°C` → OFF
2. **HEATING**: temp rising, `dT=+0.5`, `rpm=0` → HEATING
3. **IDLE**: `temp=180°C`, flat `dT`, `rpm=0` → IDLE
4. **PRODUCTION**: `rpm=20, p=8` ≥90s → PRODUCTION
5. **PRODUCTION (fallback)**: `rpm=20, p=3` or `motor_load=20%` ≥90s → PRODUCTION
6. **COOLING**: `rpm=0, dT=-0.4` → COOLING
7. **SENSOR_FAULT**: missing/NaN/implausible values → SENSOR_FAULT

### Run Tests
```bash
cd AI_Predictive_Maintaince
python test_machine_state.py
```

## 📈 Process Evaluation (PRODUCTION only)

### Traffic Light System
- **Green**: All parameters normal, baseline within limits
- **Yellow**: Minor deviations, attention needed
- **Red**: Critical deviations, immediate action required

### Baseline Comparison
- Compare current parameters to learned baseline
- Detect gradual degradation
- Trend analysis and prediction

### Anomaly Detection
- AI-powered anomaly detection
- Feature extraction (25 features)
- Confidence scoring and recommendations

## 🔧 Configuration

### Per-Machine Thresholds
Each machine can have custom thresholds:
```json
{
  "machine_id": "extruder-01",
  "rpm_on": 4.0,
  "rpm_prod": 12.0,
  "p_prod": 6.0,
  "t_min_active": 65.0,
  "production_enter_time": 120
}
```

### Calibration Tips
- Tune `P_PROD` based on typical production pressure
- Adjust `MOTOR_LOAD_MIN` per machine specifications
- Modify temperature rates for specific processes
- Set appropriate hysteresis times for your use case

## 🚀 Deployment

### Database Migration
```bash
cd backend
alembic upgrade head
```

### Environment Variables
No additional environment variables required - uses existing configuration.

### Service Restart
```bash
docker-compose restart backend
```

## 📊 Monitoring

### Health Checks
- System health: `/api/health`
- AI service: `/api/ai/status`
- MQTT status: `/api/mqtt/status`

### Logs
```bash
docker-compose logs backend | grep "state"
```

### Metrics
- State transition counts
- Time in each state
- Process evaluation results
- Alert generation rates

## 🎯 Benefits

1. **Reduced False Alarms**: Process evaluation only during actual production
2. **Improved Reliability**: Hysteresis prevents state oscillation
3. **Better Context**: Clear understanding of machine operational phase
4. **Flexible Configuration**: Per-machine threshold customization
5. **Comprehensive Monitoring**: Full state lifecycle tracking
6. **Production Focus**: Resources concentrated on production monitoring

## 🔮 Future Enhancements

1. **Machine Learning**: Adaptive threshold learning
2. **Predictive Transitions**: Predict state changes before they occur
3. **Energy Optimization**: State-based energy monitoring
4. **Maintenance Scheduling**: State-aware maintenance planning
5. **Production Analytics**: Advanced production insights

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: 2025-02-03
