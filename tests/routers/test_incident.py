import pytest
from uuid import uuid4, UUID
import jwt
from datetime import datetime, timedelta

from app.models.model import Incident
from app.schemas.incident import IncidentState, IncidentChannel, IncidentPriority

SECRET_KEY = "secret_key"
ALGORITHM = "HS256"

def create_test_token(user_id: UUID, user_type: str):
    token_data = {
        "sub": str(user_id),
        "user_type": user_type
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

def create_test_incidents(db_session, user_id: UUID, company_id: UUID, count: int = 5):
    incidents = []
    for i in range(count):
        incident = Incident(
            id=uuid4(),
            description=f"Test incident {i+1}",
            state=IncidentState.OPEN.value,
            channel=IncidentChannel.EMAIL.value,
            priority=IncidentPriority.MEDIUM.value,
            user_id=user_id,
            company_id=company_id,
            creation_date=datetime.utcnow() - timedelta(days=i)
        )
        incidents.append(incident)
    
    db_session.add_all(incidents)
    db_session.commit()
    return incidents

@pytest.fixture
def user_and_company():
    return uuid4(), uuid4()

def test_get_user_company_incidents_success(client, db_session, user_and_company):
    user_id, company_id = user_and_company
    
    create_test_incidents(db_session, user_id, company_id, 5)
    
    token = create_test_token(user_id, "user")
    response = client.post(
        "/incident-query/user-company",
        json={"user_id": str(user_id), "company_id": str(company_id)},
        headers={"authorization": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    for incident in data:
        assert UUID(incident["id"])
        assert incident["state"] == IncidentState.OPEN.value
        assert "creation_date" in incident

def test_get_user_company_incidents_unauthorized(client, user_and_company):
    user_id, company_id = user_and_company
    
    response = client.post(
        "/incident-query/user-company",
        json={"user_id": str(user_id), "company_id": str(company_id)}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"

def test_get_user_company_incidents_wrong_user(client, user_and_company):
    user_id, company_id = user_and_company
    other_user_id = uuid4()
    
    token = create_test_token(other_user_id, "user")
    response = client.post(
        "/incident-query/user-company",
        json={"user_id": str(user_id), "company_id": str(company_id)},
        headers={"authorization": token}
    )
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to access this data"

def test_get_user_company_incidents_as_manager(client, db_session, user_and_company):
    user_id, company_id = user_and_company
    manager_id = uuid4()
    
    create_test_incidents(db_session, user_id, company_id, 5)
    
    token = create_test_token(manager_id, "manager")
    response = client.post(
        "/incident-query/user-company",
        json={"user_id": str(user_id), "company_id": str(company_id)},
        headers={"authorization": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

def test_get_user_company_incidents_no_incidents(client, user_and_company):
    user_id, company_id = user_and_company
    
    token = create_test_token(user_id, "user")
    response = client.post(
        "/incident-query/user-company",
        json={"user_id": str(user_id), "company_id": str(company_id)},
        headers={"authorization": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

def test_get_user_company_incidents_limit(client, db_session, user_and_company):
    user_id, company_id = user_and_company
    
    create_test_incidents(db_session, user_id, company_id, 25)
    
    token = create_test_token(user_id, "user")
    response = client.post(
        "/incident-query/user-company",
        json={"user_id": str(user_id), "company_id": str(company_id)},
        headers={"authorization": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 20  # Check that it's limited to 20 incidents

def test_get_user_company_incidents_order(client, db_session, user_and_company):
    user_id, company_id = user_and_company
    
    create_test_incidents(db_session, user_id, company_id, 5)
    
    token = create_test_token(user_id, "user")
    response = client.post(
        "/incident-query/user-company",
        json={"user_id": str(user_id), "company_id": str(company_id)},
        headers={"authorization": f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    data = response.json()
    creation_dates = [incident["creation_date"] for incident in data]
    assert creation_dates == sorted(creation_dates, reverse=True)  # Check descending order