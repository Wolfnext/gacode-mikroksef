"""Tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client: TestClient):
        """Test main health endpoint returns correct structure."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["environment"] == "test"
        assert "ksefApi" in data
        assert "sessionActive" in data
        assert "version" in data

    def test_readiness_check(self, client: TestClient):
        """Test readiness probe."""
        response = client.get("/api/health/ready")

        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_liveness_check(self, client: TestClient):
        """Test liveness probe."""
        response = client.get("/api/health/live")

        assert response.status_code == 200
        assert response.json()["status"] == "live"
