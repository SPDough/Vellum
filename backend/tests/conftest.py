"""
Pytest configuration and fixtures for Otomeshon Banking Platform tests
"""

import os
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test environment before any imports
os.environ["ENVIRONMENT"] = "testing"

from app.main_simple import app as simple_app
from app.core.config import get_settings
from app.core.database import get_db, Base


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_otomeshon.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        # Clean up - drop all tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    simple_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(simple_app) as test_client:
        yield test_client
    
    # Clean up
    simple_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(test_db):
    """Create an async test client"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    simple_app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=simple_app, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    simple_app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Get test configuration settings"""
    return get_settings()


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing"""
    return {
        "trade_id": "TRD-001",
        "symbol": "AAPL",
        "quantity": 100,
        "price": 150.00,
        "side": "BUY",
        "trade_date": "2024-01-15",
        "settlement_date": "2024-01-17",
        "counterparty": "BROKER-A",
        "account": "ACCT-12345"
    }


@pytest.fixture  
def sample_sop_data():
    """Sample SOP data for testing"""
    return {
        "title": "Equity Trade Settlement",
        "document_number": "SOP-TS-001",
        "version": "1.0",
        "category": "Trade Settlement",
        "business_area": "Custody Operations",
        "process_type": "Semi-Automated",
        "content": """
# Equity Trade Settlement Procedure

## Purpose
This procedure defines the complete process for settling equity trades.

## Steps
1. Trade Validation
2. Confirmation Generation  
3. Settlement Instructions
4. Final Settlement
        """,
        "summary": "Complete procedure for equity trade settlement",
        "created_by": "test-user"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@otomeshon.ai",
        "username": "testuser",
        "full_name": "Test User",
        "role": "analyst",
        "department": "Testing",
        "is_active": True
    }


@pytest.fixture
def auth_headers():
    """Authentication headers for API testing"""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_redis():
    """Mock Redis connection for testing"""
    class MockRedis:
        def __init__(self):
            self._data = {}
        
        async def get(self, key):
            return self._data.get(key)
        
        async def set(self, key, value, ex=None):
            self._data[key] = value
        
        async def delete(self, key):
            self._data.pop(key, None)
        
        async def ping(self):
            return True
        
        async def close(self):
            pass
    
    return MockRedis()


@pytest.fixture
def mock_kafka():
    """Mock Kafka producer for testing"""
    class MockKafkaProducer:
        def __init__(self):
            self.messages = []
        
        async def send(self, topic, value, key=None):
            self.messages.append({
                "topic": topic,
                "value": value,
                "key": key
            })
        
        async def stop(self):
            pass
    
    return MockKafkaProducer()


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j driver for testing"""
    class MockNeo4jSession:
        async def run(self, query, parameters=None):
            # Mock result
            class MockResult:
                async def single(self):
                    return {"message": "Neo4j connected"}
            
            return MockResult()
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    class MockNeo4jDriver:
        def session(self):
            return MockNeo4jSession()
        
        async def close(self):
            pass
    
    return MockNeo4jDriver()


@pytest.fixture
def banking_compliance_data():
    """Sample data for banking compliance testing"""
    return {
        "audit_requirements": {
            "retention_days": 2555,  # 7 years
            "required_fields": ["user_id", "action", "timestamp", "details"],
            "encryption_required": True
        },
        "transaction_limits": {
            "max_amount": 10000000,  # $10M
            "daily_limit": 50000000,  # $50M
            "currency_restrictions": ["USD", "EUR", "GBP"]
        },
        "risk_parameters": {
            "max_position_size": 100000000,  # $100M
            "concentration_limit": 0.15,  # 15%
            "var_limit": 1000000  # $1M
        }
    }


@pytest.fixture
def sample_workflow_data():
    """Sample workflow execution data"""
    return {
        "workflow_name": "Trade Settlement Workflow",
        "workflow_type": "BANKING_OPERATION",
        "input_parameters": {
            "trade_id": "TRD-001",
            "settlement_type": "DVP",  # Delivery vs Payment
            "priority": "HIGH"
        },
        "steps": [
            {
                "step_id": "validate_trade",
                "step_name": "Trade Validation",
                "step_type": "AUTOMATED",
                "timeout_seconds": 30
            },
            {
                "step_id": "generate_confirmation",
                "step_name": "Generate Confirmation",
                "step_type": "AUTOMATED", 
                "timeout_seconds": 60
            },
            {
                "step_id": "settlement_instruction",
                "step_name": "Settlement Instruction",
                "step_type": "MANUAL",
                "timeout_seconds": 300
            }
        ]
    }


# Pytest markers for test categorization
pytest_markers = [
    "unit: Unit tests",
    "integration: Integration tests", 
    "banking: Banking-specific tests",
    "security: Security tests",
    "performance: Performance tests",
    "compliance: Regulatory compliance tests",
    "slow: Slow running tests"
]