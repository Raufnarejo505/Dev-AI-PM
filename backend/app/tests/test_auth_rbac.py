"""Tests for authentication and RBAC"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_success():
    """Test successful login"""
    response = client.post(
        "/users/login",
        data={"username": "admin@example.com", "password": "admin123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_failure():
    """Test failed login"""
    response = client.post(
        "/users/login",
        data={"username": "admin@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token"""
    response = client.get("/dashboard/overview")
    assert response.status_code == 401


def test_protected_endpoint_with_token():
    """Test accessing protected endpoint with valid token"""
    # First login
    login_response = client.post(
        "/users/login",
        data={"username": "admin@example.com", "password": "admin123"},
    )
    token = login_response.json()["access_token"]
    
    # Access protected endpoint
    response = client.get(
        "/dashboard/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_admin_only_endpoint():
    """Test that admin-only endpoints reject non-admin users"""
    # Login as viewer
    login_response = client.post(
        "/users/login",
        data={"username": "viewer@example.com", "password": "viewer123"},
    )
    token = login_response.json()["access_token"]
    
    # Try to access admin-only endpoint
    response = client.post(
        "/ai/retrain",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

