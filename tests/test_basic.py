import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "system" in data
    assert "version" in data


def test_api_info():
    """Test API info endpoint"""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


def test_dashboard_page():
    """Test dashboard page loads"""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_dashboard_current_data():
    """Test dashboard current data endpoint"""
    response = client.get("/dashboard/current")
    assert response.status_code == 200
    data = response.json()
    assert "solar_power_w" in data
    assert "battery_soc_percent" in data
    assert "load_power_w" in data
    assert "grid_power_w" in data


def test_charts_page():
    """Test charts page loads"""
    response = client.get("/charts")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_control_page():
    """Test control page loads"""
    response = client.get("/control")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_settings_page():
    """Test settings page loads"""
    response = client.get("/settings")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
