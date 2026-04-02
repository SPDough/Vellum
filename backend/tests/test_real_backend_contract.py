"""
Starter contract tests for the canonical full backend in `app.main`.

These tests intentionally avoid the shared fixtures in `conftest.py`, because
those currently target `app.main_simple`.

This file is the beginning of a real-backend test split.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app as real_app


@pytest.mark.integration
@pytest.mark.real_backend
class TestRealBackendContract:
    """Smoke-level contract tests for the canonical full backend."""

    def test_health_endpoint(self):
        with TestClient(real_app) as client:
            response = client.get('/health')
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            assert data['service'] == 'otomeshon-api'
            assert data['version'] == '1.0.0'

    def test_root_endpoint(self):
        with TestClient(real_app) as client:
            response = client.get('/')
            assert response.status_code == 200
            data = response.json()
            assert 'docs' in data
            assert 'health' in data
            assert data['docs'] == '/docs'
            assert data['health'] == '/health'

    def test_openapi_contains_api_v1_paths(self):
        schema = real_app.openapi()
        paths = schema.get('paths', {})
        assert isinstance(paths, dict)
        assert any(path.startswith('/api/v1') for path in paths.keys())

    def test_openapi_contains_expected_core_prefixes(self):
        schema = real_app.openapi()
        paths = schema.get('paths', {})

        expected_prefixes = [
            '/api/v1/auth',
            '/api/v1/data-sandbox',
            '/api/v1/workflow-execution',
            '/api/v1/sop-management',
            '/api/v1/rules',
        ]

        for prefix in expected_prefixes:
            assert any(path.startswith(prefix) for path in paths.keys()), f'Missing OpenAPI path prefix: {prefix}'

    def test_openapi_does_not_present_demo_auth_prefix_as_primary(self):
        schema = real_app.openapi()
        paths = schema.get('paths', {})
        assert '/api/auth/login' not in paths
        assert '/api/auth/me' not in paths
        assert '/api/auth/logout' not in paths

    def test_openapi_includes_real_auth_contract_paths(self):
        schema = real_app.openapi()
        paths = schema.get('paths', {})

        expected_paths = [
            '/api/v1/auth/login',
            '/api/v1/auth/logout',
            '/api/v1/auth/me',
            '/api/v1/auth/config',
            '/api/v1/auth/providers',
        ]

        for expected_path in expected_paths:
            assert expected_path in paths, f'Missing expected real-backend auth path: {expected_path}'

    def test_openapi_metadata_matches_full_backend_identity(self):
        schema = real_app.openapi()
        assert schema.get('info', {}).get('title') == 'Otomeshon'
        assert schema.get('info', {}).get('version') == '1.0.0'
