# app/routers/incident.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from enum import Enum

class IncidentState(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    ESCALATED = "escalated"
    
class IncidentChannel(str, Enum):
    PHONE = "phone"
    EMAIL = "email"
    CHAT = "chat"
    MOBILE = "mobile"
    
class IncidentPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    
class IncidentResponse(BaseModel):
    id: UUID
    description: str
    state: IncidentState
    creation_date: datetime
    
class UserCompanyRequest(BaseModel):
    user_id: UUID
    company_id: UUID

class IncidentDetailedResponse(BaseModel):
    id: UUID
    description: str
    state: IncidentState
    channel: IncidentChannel
    priority: IncidentPriority
    creation_date: datetime
    user_id: UUID
    company_id: UUID
    manager_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }

class IncidentHistoryResponse(BaseModel):
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class IncidentDetailedWithHistoryResponse(IncidentDetailedResponse):
    history: List[IncidentHistoryResponse] = []

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }