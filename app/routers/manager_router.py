# routers/manager_router.py

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List
from datetime import datetime, timedelta
from uuid import UUID

from ..session import get_db
from ..models.model import Incident, IncidentHistory
from ..schemas.incident import (
    IncidentDetailedResponse,
    IncidentDetailedWithHistoryResponse
)
import os
import jwt

router = APIRouter(prefix="/incident-query/manager", tags=["Manager"])

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'secret_key')
ALGORITHM = "HS256"

def get_current_user(authorization: str = Header(None)):
    if authorization is None:
        return None
    try:
        token = authorization.replace('Bearer ', '') if authorization.startswith('Bearer ') else authorization
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

@router.get("/assigned-incidents", response_model=List[IncidentDetailedResponse])
def get_assigned_incidents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if current_user['user_type'] != 'manager':
        raise HTTPException(status_code=403, detail="Not authorized to access this data")
    
    manager_id = UUID(current_user['sub'])

    incidents = (
        db.query(Incident)
        .filter(Incident.manager_id == manager_id)
        .order_by(Incident.creation_date.desc())
        .all()
    )
    return incidents

@router.get("/daily-stats")
def get_manager_daily_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get daily stats for a manager:
    - incidentsHandled: Total incidents assigned to the manager and closed today.
    - avgResolutionTime: Mock value for average resolution time.
    - customerSatisfaction: Mock value for customer satisfaction.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if current_user['user_type'] != 'manager':
        raise HTTPException(status_code=403, detail="Not authorized to access this data")

    manager_id = UUID(current_user['sub'])

    incidents_handled = (
        db.query(func.count(Incident.id))
        .filter(
            Incident.manager_id == manager_id,
            Incident.state == 'closed'
        )
        .scalar()
    )

    # Mocked average resolution time
    avg_resolution_time = "15 mins"

    # Mocked customer satisfaction value
    customer_satisfaction = 4.8

    return {
        "incidentsHandled": incidents_handled,
        "avgResolutionTime": avg_resolution_time,
        "customerSatisfaction": customer_satisfaction
    }


@router.get("/high-priority-assigned-incidents", response_model=List[IncidentDetailedWithHistoryResponse])
def get_high_priority_assigned_incidents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch high-priority incidents assigned to the manager, including user, company, and history details.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if current_user['user_type'] != 'manager':
        raise HTTPException(status_code=403, detail="Not authorized to access this data")
    
    manager_id = UUID(current_user['sub'])

    incidents = (
        db.query(Incident)
        .filter(
            Incident.manager_id == manager_id,
            Incident.priority == 'high'
        )
        .order_by(Incident.creation_date.desc())
        .all()
    )
    
    response = []
    for incident in incidents:
        history = (
            db.query(IncidentHistory)
            .filter(IncidentHistory.incident_id == incident.id)
            .order_by(IncidentHistory.created_at.asc())
            .all()
        )
        
        detailed_incident = {
            **incident.__dict__,
            "history": history
        }
        response.append(detailed_incident)
    
    return response
