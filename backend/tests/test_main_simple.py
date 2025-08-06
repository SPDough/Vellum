"""
Tests for the simplified main application
"""
import sys
import os
import pytest
from fastapi.testclient import TestClient
from app.main_simple import app, generate_sample_data

# Add parent directory for shared test utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
try:
    from test_utils import assert_health_response
except ImportError:
    # Fallback if import fails
    def assert_health_response(response, expected_status_code=200):
        assert response.status_code == expected_status_code
        data = response.json()
        assert "active_connections" in data
        assert "messages_sent" in data
        assert "last_activity" in data

# Generate sample data before running tests
generate_sample_data()

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "otomeshon-simple"


def test_get_records():
    """Test getting data sandbox records"""
    response = client.get("/api/v1/data-sandbox/records")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["data"], list)
    assert data["total"] > 0  # Should have sample data


def test_get_records_with_pagination():
    """Test pagination parameters"""
    response = client.get("/api/v1/data-sandbox/records?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["data"]) <= 10


def test_get_data_sources():
    """Test getting available data sources"""
    response = client.get("/api/v1/data-sandbox/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0


def test_get_stats():
    """Test getting data sandbox statistics"""
    response = client.get("/api/v1/data-sandbox/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert "sources" in data
    assert data["total_records"] > 0
    assert isinstance(data["sources"], dict)


def test_filter_records():
    """Test filtering records"""
    filter_request = {
        "page": 1,
        "page_size": 20,
        "sort_by": "timestamp",
        "sort_order": "desc"
    }
    response = client.post("/api/v1/data-sandbox/filter", json=filter_request)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert len(data["data"]) <= 20


def test_export_data():
    """Test data export endpoint"""
    export_request = {"format": "csv"}
    response = client.post("/api/v1/data-sandbox/export", json=export_request)
    assert response.status_code == 200
    data = response.json()
    assert "export_id" in data
    assert "format" in data
    assert "status" in data
    assert data["format"] == "csv"
    assert data["status"] == "processing"


def test_websocket_stats():
    """Test WebSocket stats endpoint"""
    response = client.get("/api/v1/data-sandbox/ws/stats")
    assert_health_response(response)


def test_metrics():
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "otomeshon_websocket_connections_total" in data
    assert "otomeshon_data_sandbox_records_total" in data
    assert "otomeshon_data_exports_total" in data
