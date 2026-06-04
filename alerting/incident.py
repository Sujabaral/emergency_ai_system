# alerting/incident.py
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

class EventSource(str, Enum):
    SENTRY       = "sentry"
    UPTIME_ROBOT = "uptime_robot"
    LOGS         = "logs"
    DB           = "db"
    TICKET       = "ticket"
    UNKNOWN      = "unknown"

class Severity(str, Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low
      
# Data models
@dataclass
class RawEvent:
    source: EventSource
    message: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Incident:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Stable unique ID 
    #source of incident from event
    source: EventSource = EventSource.UNKNOWN
    message: str = ""
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    
    severity: Severity = Severity.P4
    classification_route: str = "rule_classifier"
    confidence: float = 0.0
    processing_notes: list[str] = field(default_factory=list)
    acknowledged: bool = False
    resolved: bool = False

    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
