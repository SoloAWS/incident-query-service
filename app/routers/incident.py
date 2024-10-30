# app/routers/incident.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..schemas.incident import (
    IncidentDetailedResponse,
    IncidentDetailedWithHistoryResponse,
    IncidentResponse,
    UserCompanyRequest
)
from ..models.model import Incident, IncidentHistory
from ..session import get_db
from typing import List
import os
import jwt

router = APIRouter(prefix="/incident-query", tags=["Incident"])

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'secret_key')
ALGORITHM = "HS256"

def get_current_user(token: str = Header(None)):
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

@router.post("/user-company", response_model=List[IncidentResponse])
def get_user_company_incidents(
    data: UserCompanyRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
       raise HTTPException(status_code=401, detail="Authentication required")

    if current_user['user_type'] != 'manager' and current_user['sub'] != str(data.user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this data")

    incidents = db.query(Incident).filter(
        Incident.user_id == data.user_id,
        Incident.company_id == data.company_id
    ).order_by(Incident.creation_date.desc()).limit(20).all()
    return incidents

@router.get("/all-incidents", response_model=List[IncidentDetailedResponse])
def get_all_incidents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
    ):
    if not current_user:
       raise HTTPException(status_code=401, detail="Authentication required")

    if current_user['user_type'] != 'manager':
        raise HTTPException(status_code=403, detail="Not authorized to access this data")
    
    incidents = db.query(Incident).order_by(Incident.creation_date.desc()).all()
    return incidents

@router.get("/{incident_id}", response_model=IncidentDetailedWithHistoryResponse)
def get_incident_by_id(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
    ):
    if not current_user:
       raise HTTPException(status_code=401, detail="Authentication required")

    if current_user['user_type'] != 'manager':
        raise HTTPException(status_code=403, detail="Not authorized to access this data")
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    history = (
        db.query(IncidentHistory)
        .filter(IncidentHistory.incident_id == incident_id)
        .order_by(IncidentHistory.created_at.asc())
        .all()
    )
    
    response = incident.__dict__
    response['history'] = history
    
    return response