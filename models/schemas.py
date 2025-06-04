"""
Pydantic models and schemas for the multi-agent system.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, EmailStr, validator


class FormatType(str, Enum):
    """Supported input formats."""
    EMAIL = "email"
    JSON = "json"
    PDF = "pdf"


class BusinessIntent(str, Enum):
    """Business intent classifications."""
    RFQ = "rfq"  # Request for Quote
    COMPLAINT = "complaint"
    INVOICE = "invoice"
    REGULATION = "regulation"
    FRAUD_RISK = "fraud_risk"


class ToneType(str, Enum):
    """Email tone classifications."""
    POLITE = "polite"
    NEUTRAL = "neutral"
    URGENT = "urgent"
    ANGRY = "angry"
    THREATENING = "threatening"
    ESCALATION = "escalation"


class UrgencyLevel(str, Enum):
    """Urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    """Available action types."""
    ESCALATE = "escalate"
    LOG_AND_CLOSE = "log_and_close"
    FLAG_ANOMALY = "flag_anomaly"
    COMPLIANCE_ALERT = "compliance_alert"
    RISK_ALERT = "risk_alert"
    CREATE_TICKET = "create_ticket"


class ClassificationResult(BaseModel):
    """Result from the classifier agent."""
    format_type: FormatType
    business_intent: BusinessIntent
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmailData(BaseModel):
    """Structured email data."""
    sender: EmailStr
    recipient: Optional[EmailStr] = None
    subject: str
    body: str
    timestamp: Optional[datetime] = None
    attachments: List[str] = Field(default_factory=list)


class EmailAnalysis(BaseModel):
    """Email analysis results."""
    tone: ToneType
    urgency: UrgencyLevel
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    key_phrases: List[str] = Field(default_factory=list)
    issue_category: Optional[str] = None
    requires_escalation: bool = False
    extracted_entities: Dict[str, List[str]] = Field(default_factory=dict)


class JSONValidationResult(BaseModel):
    """JSON validation results."""
    is_valid: bool
    schema_errors: List[str] = Field(default_factory=list)
    anomalies: List[str] = Field(default_factory=list)
    anomaly_score: float = Field(ge=0.0, le=1.0)
    missing_fields: List[str] = Field(default_factory=list)
    type_errors: List[str] = Field(default_factory=list)


class PDFAnalysis(BaseModel):
    """PDF analysis results."""
    document_type: str
    extracted_text: str
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    compliance_flags: List[str] = Field(default_factory=list)
    risk_indicators: List[str] = Field(default_factory=list)
    invoice_total: Optional[float] = None
    line_items: List[Dict[str, Any]] = Field(default_factory=list)


class AgentDecision(BaseModel):
    """Agent decision trace."""
    agent_name: str
    input_data: Dict[str, Any]
    decision: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: Optional[float] = None


class ActionRequest(BaseModel):
    """Action router request."""
    action_type: ActionType
    payload: Dict[str, Any]
    priority: UrgencyLevel = UrgencyLevel.MEDIUM
    source_agent: str
    correlation_id: str


class ActionResult(BaseModel):
    """Action execution result."""
    action_id: str
    action_type: ActionType
    status: str  # success, failed, pending
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: Optional[float] = None


class ProcessingSession(BaseModel):
    """Complete processing session."""
    session_id: str
    input_metadata: Dict[str, Any]
    classification: ClassificationResult
    agent_decisions: List[AgentDecision] = Field(default_factory=list)
    actions_triggered: List[ActionResult] = Field(default_factory=list)
    final_status: str
    total_processing_time_ms: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class MemoryEntry(BaseModel):
    """Shared memory entry."""
    key: str
    value: Any
    entry_type: str
    agent_source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ttl_seconds: Optional[int] = None


class SystemHealth(BaseModel):
    """System health status."""
    status: str
    agents_status: Dict[str, str]
    memory_status: str
    action_router_status: str
    last_check: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: float
    processed_sessions: int
    error_count: int


# Sample schemas for validation
WEBHOOK_SCHEMA = {
    "type": "object",
    "required": ["event_type", "timestamp", "data"],
    "properties": {
        "event_type": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "data": {
            "type": "object",
            "required": ["user_id", "amount"],
            "properties": {
                "user_id": {"type": "string"},
                "amount": {"type": "number"},
                "currency": {"type": "string"},
                "transaction_id": {"type": "string"}
            }
        }
    }
}

INVOICE_SCHEMA = {
    "type": "object",
    "required": ["invoice_number", "total", "line_items"],
    "properties": {
        "invoice_number": {"type": "string"},
        "total": {"type": "number"},
        "currency": {"type": "string"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["description", "quantity", "unit_price"],
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "number"}
                }
            }
        }
    }
}
