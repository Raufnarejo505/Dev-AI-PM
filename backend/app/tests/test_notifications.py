import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers.notifications import router
from app.services import notification_service


@pytest.fixture
def test_client(monkeypatch):
    app = FastAPI()
    app.include_router(router)

    # Ensure email is considered configured for the duration of the test
    monkeypatch.setattr(notification_service, "email_configured", lambda: True)
    notification_service.EMAIL_AVAILABLE = True
    notification_service.EMAIL_LAST_ERROR = None

    async def fake_verify():
        notification_service.EMAIL_AVAILABLE = True
        notification_service.EMAIL_LAST_ERROR = None
        return True

    async def fake_send(to=None):
        return True, None

    monkeypatch.setattr(notification_service, "verify_email_transport", fake_verify)
    monkeypatch.setattr(notification_service, "send_test_email", fake_send)

    return TestClient(app)


def test_test_email_endpoint_success(test_client):
    response = test_client.post("/notifications/test-email", json={"to": "demo@example.com"})
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "message" in response.json()

