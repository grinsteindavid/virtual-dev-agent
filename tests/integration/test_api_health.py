"""Integration tests for API health endpoint."""

import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require RUN_INTEGRATION_TESTS=1"
)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_returns_ok(self):
        """Test that health endpoint returns OK status."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_health_includes_version(self):
        """Test that health endpoint includes version."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert "version" in response.json()
