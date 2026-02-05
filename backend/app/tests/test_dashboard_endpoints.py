"""Tests for dashboard endpoints"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_auth_token(username="admin@example.com", password="admin123"):
    """Helper to get auth token"""
    response = client.post(
        "/users/login",
        data={"username": username, "password": password},
    )
    return response.json()["access_token"]


def test_dashboard_overview():
    """Test dashboard overview endpoint"""
    token = get_auth_token()
    response = client.get(
        "/dashboard/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "machines" in data
    assert "sensors" in data
    assert "alarms" in data
    assert "predictions" in data


def test_dashboard_machines_stats():
    """Test machines stats endpoint"""
    token = get_auth_token()
    response = client.get(
        "/dashboard/machines/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "by_status" in data
    assert "by_criticality" in data


def test_dashboard_predictions_stats():
    """Test predictions stats endpoint"""
    token = get_auth_token()
    response = client.get(
        "/dashboard/predictions/stats?hours=24",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_status" in data
    assert "period_hours" in data

