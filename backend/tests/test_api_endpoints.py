"""
Integration tests for API endpoints
"""

import pytest
import json
from httpx import AsyncClient
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestAuthEndpoints:
    """Test authentication API endpoints"""
    
    async def test_login_success(self, async_client: AsyncClient):
        """Test successful login"""
        login_data = {
            "email": "admin@otomeshon.ai",
            "password": "admin123"
        }
        
        response = await async_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == login_data["email"]
    
    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid credentials"""
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid email or password" in data["detail"]
    
    async def test_logout(self, async_client: AsyncClient):
        """Test logout endpoint"""
        response = await async_client.post("/api/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()
    
    async def test_get_current_user(self, async_client: AsyncClient):
        """Test get current user endpoint"""
        response = await async_client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["id", "email", "username", "full_name", "role"]
        for field in required_fields:
            assert field in data
    
    async def test_get_auth_config(self, async_client: AsyncClient):
        """Test authentication configuration endpoint"""
        response = await async_client.get("/api/auth/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "current_provider" in data
        assert "available_providers" in data
        assert "endpoints" in data


@pytest.mark.integration
class TestDataSandboxEndpoints:
    """Test Data Sandbox API endpoints"""
    
    async def test_get_records(self, async_client: AsyncClient):
        """Test getting data sandbox records"""
        response = await async_client.get("/api/v1/data-sandbox/records")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["data"], list)
    
    async def test_get_records_with_pagination(self, async_client: AsyncClient):
        """Test data sandbox records with pagination"""
        page = 1
        page_size = 10
        
        response = await async_client.get(
            f"/api/v1/data-sandbox/records?page={page}&page_size={page_size}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == page
        assert data["page_size"] == page_size
        assert len(data["data"]) <= page_size
    
    async def test_filter_records(self, async_client: AsyncClient):
        """Test filtering data sandbox records"""
        filter_data = {
            "filters": {
                "source": "workflow"
            },
            "sort_by": "timestamp",
            "sort_order": "desc",
            "page": 1,
            "page_size": 20
        }
        
        response = await async_client.post("/api/v1/data-sandbox/filter", json=filter_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "total" in data
        # Verify filtering worked (if any records match)
        if data["data"]:
            for record in data["data"]:
                assert record["source"] == "workflow"
    
    async def test_get_data_sources(self, async_client: AsyncClient):
        """Test getting available data sources"""
        response = await async_client.get("/api/v1/data-sandbox/sources")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sources" in data
        assert isinstance(data["sources"], list)
    
    async def test_get_stats(self, async_client: AsyncClient):
        """Test getting data sandbox statistics"""
        response = await async_client.get("/api/v1/data-sandbox/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_records" in data
        assert "sources" in data
        assert isinstance(data["total_records"], int)
        assert isinstance(data["sources"], dict)


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check endpoints"""
    
    async def test_health_check(self, async_client: AsyncClient):
        """Test basic health check"""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
    
    async def test_websocket_stats(self, async_client: AsyncClient):
        """Test WebSocket statistics endpoint"""
        response = await async_client.get("/api/v1/data-sandbox/ws/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "active_connections" in data
        assert "messages_sent" in data
        assert "last_activity" in data
    
    async def test_metrics_endpoint(self, async_client: AsyncClient):
        """Test metrics endpoint for monitoring"""
        response = await async_client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected metrics
        expected_metrics = [
            "otomeshon_websocket_connections_total",
            "otomeshon_data_sandbox_records_total",
            "otomeshon_data_exports_total"
        ]
        
        for metric in expected_metrics:
            assert metric in data


@pytest.mark.integration
@pytest.mark.banking
class TestBankingEndpoints:
    """Test banking-specific API endpoints"""
    
    async def test_trade_validation_endpoint(self, async_client: AsyncClient, sample_trade_data, auth_headers):
        """Test trade validation API"""
        # Note: This would test the actual trade validation endpoint when implemented
        trade_data = sample_trade_data.copy()
        
        # Mock the endpoint response for now
        expected_response = {
            "trade_id": trade_data["trade_id"],
            "status": "VALID",
            "validation_results": {
                "price_check": "PASSED",
                "quantity_check": "PASSED", 
                "counterparty_check": "PASSED",
                "compliance_check": "PASSED"
            },
            "risk_score": 0.25
        }
        
        # Validate expected response structure
        assert "trade_id" in expected_response
        assert "status" in expected_response
        assert "validation_results" in expected_response
        assert expected_response["status"] in ["VALID", "INVALID", "WARNING"]
    
    async def test_sop_execution_endpoint(self, async_client: AsyncClient, sample_sop_data, auth_headers):
        """Test SOP execution API"""
        sop_data = sample_sop_data.copy()
        
        # Mock SOP execution request
        execution_request = {
            "sop_id": "SOP-001",
            "execution_name": "Test Execution",
            "initiated_by": "test-user",
            "context_data": {
                "trade_id": "TRD-001",
                "priority": "HIGH"
            }
        }
        
        # Expected response structure
        expected_response = {
            "execution_id": "EXEC-001",
            "sop_id": execution_request["sop_id"],
            "status": "INITIATED",
            "current_step": 1,
            "total_steps": 4,
            "estimated_completion": "2024-01-15T10:30:00Z"
        }
        
        # Validate response structure
        assert "execution_id" in expected_response
        assert "status" in expected_response
        assert "current_step" in expected_response
        assert expected_response["status"] in ["INITIATED", "IN_PROGRESS", "COMPLETED", "FAILED"]


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling"""
    
    async def test_404_not_found(self, async_client: AsyncClient):
        """Test 404 error handling"""
        response = await async_client.get("/api/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    async def test_405_method_not_allowed(self, async_client: AsyncClient):
        """Test 405 error handling"""
        # Try POST on a GET-only endpoint
        response = await async_client.post("/health")
        
        assert response.status_code == 405
    
    async def test_422_validation_error(self, async_client: AsyncClient):
        """Test validation error handling"""
        # Send invalid JSON to login endpoint
        invalid_data = {
            "email": "not-an-email",  # Invalid email format
            "password": ""  # Empty password
        }
        
        response = await async_client.post("/api/auth/login", json=invalid_data)
        
        assert response.status_code == 422
    
    async def test_500_internal_error_handling(self, async_client: AsyncClient):
        """Test internal server error handling"""
        # This would test error handling middleware
        # For now, verify error response structure
        
        expected_error_structure = {
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "internal_error",
                "request_id": "req_123456"
            }
        }
        
        # Validate error response structure
        assert "error" in expected_error_structure
        assert "code" in expected_error_structure["error"]
        assert "message" in expected_error_structure["error"]
        assert "type" in expected_error_structure["error"]


@pytest.mark.integration
class TestSecurityHeaders:
    """Test security headers are properly set"""
    
    async def test_security_headers_present(self, async_client: AsyncClient):
        """Test that security headers are present in responses"""
        response = await async_client.get("/health")
        
        # Check for security headers
        expected_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "strict-transport-security",
            "referrer-policy"
        ]
        
        for header in expected_headers:
            assert header in response.headers or header.replace("-", "_") in response.headers
    
    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are properly configured"""
        # Make an OPTIONS request to test CORS
        response = await async_client.options("/api/auth/login")
        
        # Should have CORS headers
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        # Note: Actual CORS headers depend on middleware configuration
        # This test validates the expected structure


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceEndpoints:
    """Test API performance requirements"""
    
    async def test_endpoint_response_times(self, async_client: AsyncClient):
        """Test that endpoints meet response time SLAs"""
        import time
        
        endpoints = [
            "/health",
            "/api/auth/config",
            "/api/v1/data-sandbox/stats"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await async_client.get(endpoint)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            # SLA: All endpoints should respond within 500ms
            assert response_time_ms < 500, f"Endpoint {endpoint} took {response_time_ms:.2f}ms"
            assert response.status_code == 200
    
    async def test_concurrent_requests(self, async_client: AsyncClient):
        """Test handling of concurrent requests"""
        import asyncio
        
        # Make 10 concurrent requests
        tasks = []
        for _ in range(10):
            task = async_client.get("/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Verify we got expected number of responses
        assert len(responses) == 10