import pytest
from uuid import uuid4, UUID
import jwt
from datetime import datetime, timedelta

from app.models.model import Incident, IncidentHistory
from app.schemas.incident import IncidentState, IncidentChannel, IncidentPriority

SECRET_KEY = "secret_key"
ALGORITHM = "HS256"

def create_test_token(user_id: UUID, user_type: str):
    token_data = {
        "sub": str(user_id),
        "user_type": user_type
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

def create_test_incidents(db_session, manager_id: UUID, count: int = 5, priority: str = "medium"):
    incidents = []
    for i in range(count):
        incident = Incident(
            id=uuid4(),
            description=f"Test incident {i+1}",
            state="open",
            channel="email",
            priority=priority,
            manager_id=manager_id,
            user_id=uuid4(),
            company_id=uuid4(),
            creation_date=datetime.utcnow() - timedelta(days=i)
        )
        incidents.append(incident)
    
    db_session.add_all(incidents)
    db_session.commit()
    return incidents

def create_test_incident_history(db_session, incident_id: UUID):
    history = IncidentHistory(
        id=uuid4(),
        incident_id=incident_id,
        description="Status updated from open to in_progress",
        created_at=datetime.utcnow()
    )
    db_session.add(history)
    db_session.commit()
    return history

# Test get_assigned_incidents endpoint
def test_get_assigned_incidents_success(client, db_session):
    manager_id = uuid4()
    incidents = create_test_incidents(db_session, manager_id, 5)
    
    token = create_test_token(manager_id, "manager")
    response = client.get(
        "/incident-query/manager/assigned-incidents",
        headers={"authorization": f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    for incident in data:
        assert UUID(incident["manager_id"]) == manager_id

def test_get_assigned_incidents_unauthorized(client):
    response = client.get("/incident-query/manager/assigned-incidents")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"

def test_get_assigned_incidents_wrong_user_type(client):
    user_id = uuid4()
    token = create_test_token(user_id, "user")
    response = client.get(
        "/incident-query/manager/assigned-incidents",
        headers={"authorization": f'Bearer {token}'}
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this data"

# Test get_manager_daily_stats endpoint
def test_get_manager_daily_stats_success(client, db_session):
    manager_id = uuid4()
    incidents = create_test_incidents(db_session, manager_id, 5)
    
    # Update some incidents to closed state for testing
    for incident in incidents[:2]:
        incident.state = "closed"
    db_session.commit()
    
    token = create_test_token(manager_id, "manager")
    response = client.get(
        "/incident-query/manager/daily-stats",
        headers={"authorization": f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "incidentsHandled" in data
    assert "avgResolutionTime" in data
    assert "customerSatisfaction" in data
    assert isinstance(data["incidentsHandled"], int)
    assert isinstance(data["avgResolutionTime"], str)
    assert isinstance(data["customerSatisfaction"], float)

def test_get_manager_daily_stats_unauthorized(client):
    response = client.get("/incident-query/manager/daily-stats")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"

def test_get_manager_daily_stats_wrong_user_type(client):
    user_id = uuid4()
    token = create_test_token(user_id, "user")
    response = client.get(
        "/incident-query/manager/daily-stats",
        headers={"authorization": f'Bearer {token}'}
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this data"

# Test get_high_priority_assigned_incidents endpoint
def test_get_high_priority_assigned_incidents_success(client, db_session):
    manager_id = uuid4()
    incidents = create_test_incidents(db_session, manager_id, 3, priority="high")
    
    # Create history for each incident
    for incident in incidents:
        create_test_incident_history(db_session, incident.id)
    
    token = create_test_token(manager_id, "manager")
    response = client.get(
        "/incident-query/manager/high-priority-assigned-incidents",
        headers={"authorization": f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for incident in data:
        assert incident["priority"] == "high"
        assert "history" in incident
        assert len(incident["history"]) > 0

def test_get_high_priority_assigned_incidents_unauthorized(client):
    response = client.get("/incident-query/manager/high-priority-assigned-incidents")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"

def test_get_high_priority_assigned_incidents_wrong_user_type(client):
    user_id = uuid4()
    token = create_test_token(user_id, "user")
    response = client.get(
        "/incident-query/manager/high-priority-assigned-incidents",
        headers={"authorization": f'Bearer {token}'}
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this data"

def test_get_high_priority_assigned_incidents_no_incidents(client, db_session):
    manager_id = uuid4()
    token = create_test_token(manager_id, "manager")
    response = client.get(
        "/incident-query/manager/high-priority-assigned-incidents",
        headers={"authorization": f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

def test_get_high_priority_assigned_incidents_order(client, db_session):
    manager_id = uuid4()
    incidents = create_test_incidents(db_session, manager_id, 3, priority="high")
    
    token = create_test_token(manager_id, "manager")
    response = client.get(
        "/incident-query/manager/high-priority-assigned-incidents",
        headers={"authorization": f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.json()
    creation_dates = [incident["creation_date"] for incident in data]
    assert creation_dates == sorted(creation_dates, reverse=True)  # Check descending order