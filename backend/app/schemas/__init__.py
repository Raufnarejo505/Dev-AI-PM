from app.schemas.alarm import AlarmCreate, AlarmRead, AlarmUpdate
from app.schemas.audit_log import AuditLogCreate, AuditLogRead
from app.schemas.machine import MachineCreate, MachineRead, MachineUpdate
from app.schemas.prediction import PredictionCreate, PredictionRead, PredictionRequest
from app.schemas.report import ReportRequest, ReportResponse
from app.schemas.sensor import SensorCreate, SensorRead, SensorUpdate
from app.schemas.sensor_data import SensorDataIn, SensorDataOut
from app.schemas.settings import SettingsCreate, SettingsRead, SettingsUpdate
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.schemas.user import Token, UserCreate, UserRead
from app.schemas.webhook import WebhookCreate, WebhookRead, WebhookUpdate

