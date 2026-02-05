// Common Types
export interface BaseEntity {
    id: string;
    created_at: string;
    updated_at: string;
}

// Machine Types
export interface MachineBase {
    name: string;
    location?: string;
    description?: string;
    status?: string;
    criticality?: string;
    metadata?: Record<string, any>;
    last_service_date?: string;
}

export interface MachineCreate extends MachineBase {}

export interface MachineUpdate extends Partial<MachineBase> {}

export interface MachineRead extends BaseEntity, MachineBase {}

// Sensor Types
export interface SensorBase {
    name: string;
    sensor_type?: string;
    unit?: string;
    machine_id: string;
    min_threshold?: number;
    max_threshold?: number;
    warning_threshold?: number;
    critical_threshold?: number;
    metadata?: Record<string, any>;
}

export interface SensorCreate extends SensorBase {}

export interface SensorUpdate extends Partial<SensorBase> {}

export interface SensorRead extends BaseEntity, SensorBase {
    latest_value?: number;
    current_value?: number;
}

// Prediction Types
export interface PredictionRequest {
    sensor_id: string;
    machine_id: string;
    timestamp: string;
    value: number;
    context?: Record<string, any>;
}

export interface PredictionCreate {
    sensor_id: string;
    machine_id: string;
    timestamp: string;
    score?: number;
    status?: string;
    anomaly_type?: string;
    model_version?: string;
    remaining_useful_life?: number;
    prediction?: string;
    confidence?: number;
    response_time_ms?: number;
    contributing_features?: Record<string, any>;
    metadata?: Record<string, any>;
}

export interface PredictionRead extends BaseEntity, PredictionCreate {}

// Alarm Types
export interface AlarmBase {
    machine_id: string;
    sensor_id?: string;
    prediction_id?: string;
    severity: string;
    message: string;
    status?: string;
    metadata?: Record<string, any>;
}

export interface AlarmCreate extends AlarmBase {}

export interface AlarmUpdate {
    status?: string;
    resolved_at?: string;
    metadata?: Record<string, any>;
}

export interface AlarmRead extends BaseEntity, AlarmBase {
    triggered_at?: string;
    resolved_at?: string;
}

// Ticket Types
export interface TicketBase {
    machine_id: string;
    alarm_id?: string;
    title: string;
    description?: string;
    priority?: string;
    status?: string;
    assigned_to?: string;
    due_date?: string;
    metadata?: Record<string, any>;
}

export interface TicketCreate extends TicketBase {}

export interface TicketUpdate extends Partial<TicketBase> {}

export interface TicketRead extends BaseEntity, TicketBase {}

// Comment Types
export interface CommentBase {
    resource_type: string;
    resource_id: string;
    content: string;
    is_internal?: boolean;
}

export interface CommentCreate extends CommentBase {}

export interface CommentRead extends BaseEntity, CommentBase {
    user_id: string;
}

// Report Types
export interface ReportRequest {
    format: "csv" | "pdf" | "xlsx";
    date_from: string;
    date_to: string;
    machine_id?: string;
    sensor_id?: string;
}

export interface ReportResponse {
    report_id: string;
    report_name: string;
    url: string;
    format: string;
}

// Dashboard Types
export interface DashboardOverview {
    machines: {
        total: number;
        online: number;
    };
    alarms: {
        active: number;
    };
    sensors: {
        total: number;
    };
    predictions: {
        last_24h: number;
    };
}

// AI Service Types
export interface AIStatus {
    status: string;
    model_loaded: boolean;
    model_version?: string;
    buffers?: number;
    performance?: {
        predictions_total: number;
        predictions_per_second: number;
        avg_response_time_ms: number;
    };
}

// MQTT Types
export interface MQTTStatus {
    connected: boolean;
    broker?: {
        host: string;
        port: number;
    };
    consumer?: {
        connected: boolean;
        topics?: string[];
        queue_size?: number;
    };
}

// Settings Types
export interface SettingBase {
    key: string;
    value: string;
    category?: string;
    description?: string;
}

export interface SettingCreate extends SettingBase {}

export interface SettingUpdate {
    value?: string;
    description?: string;
}

export interface SettingRead extends BaseEntity, SettingBase {}

// Webhook Types
export interface WebhookBase {
    name: string;
    url: string;
    events: string[];
    is_active?: boolean;
    timeout_seconds?: number;
    headers?: Record<string, string>;
}

export interface WebhookCreate extends WebhookBase {}

export interface WebhookUpdate extends Partial<WebhookBase> {}

export interface WebhookRead extends BaseEntity, WebhookBase {}

// Role Types
export interface RoleBase {
    name: string;
    description?: string;
    permissions?: string[];
}

export interface RoleCreate extends RoleBase {}

export interface RoleUpdate extends Partial<RoleBase> {}

export interface RoleRead extends BaseEntity, RoleBase {}

// User Types
export interface UserBase {
    email: string;
    full_name?: string;
    role?: string;
    is_active?: boolean;
    password?: string;
}

export interface UserCreate extends UserBase {
    password: string;
}

export interface UserUpdate extends Partial<UserBase> {
    password?: string;
}

export interface UserRead extends BaseEntity, UserBase {}

