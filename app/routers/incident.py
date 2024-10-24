# app/routers/incident.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..schemas.incident import (
    IncidentResponse,
    UserCompanyRequest
)
from ..models.model import Incident
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
    #current_user: dict = Depends(get_current_user)
):
    # if not current_user:
    #    raise HTTPException(status_code=401, detail="Authentication required")

    # if current_user['user_type'] != 'manager' and current_user['sub'] != str(data.user_id):
    #     raise HTTPException(status_code=403, detail="Not authorized to access this data")

    incidents = db.query(Incident).filter(
        Incident.user_id == data.user_id,
        Incident.company_id == data.company_id
    ).order_by(Incident.creation_date.desc()).limit(20).all()
    return incidents