"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_init_session_success(self, client: TestClient, mock_ksef_client, mock_crypto_service):
        """Test successful session initialization."""
        response = client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        assert response.status_code == 201
        data = response.json()

        assert "sessionToken" in data
        assert "referenceNumber" in data
        assert "timestamp" in data

    def test_init_session_invalid_nip(self, client: TestClient):
        """Test session init with invalid NIP."""
        response = client.post(
            "/api/auth/session/init-token",
            json={"nip": "123"}  # Too short
        )

        assert response.status_code == 422  # Validation error

    def test_init_session_missing_nip(self, client: TestClient):
        """Test session init without NIP."""
        response = client.post(
            "/api/auth/session/init-token",
            json={}
        )

        assert response.status_code == 422

    def test_get_session_status_no_session(self, client: TestClient):
        """Test getting status when no session exists."""
        response = client.get("/api/auth/session/status")

        assert response.status_code == 404
        assert "No active session" in response.json()["detail"]

    def test_get_session_status_with_session(
        self, client: TestClient, mock_ksef_client, mock_crypto_service
    ):
        """Test getting status with active session."""
        # First init a session
        client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        # Then get status
        response = client.get("/api/auth/session/status")

        assert response.status_code == 200
        data = response.json()

        assert "referenceNumber" in data
        assert "processingCode" in data
        assert data["isActive"] is True

    def test_terminate_session_no_session(self, client: TestClient):
        """Test terminating when no session exists."""
        response = client.post("/api/auth/session/terminate")

        assert response.status_code == 404

    def test_terminate_session_success(
        self, client: TestClient, mock_ksef_client, mock_crypto_service
    ):
        """Test successful session termination."""
        # First init a session
        client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        # Then terminate
        response = client.post("/api/auth/session/terminate")

        assert response.status_code == 200
        assert "terminated" in response.json()["message"].lower()

    def test_get_session_info_no_session(self, client: TestClient):
        """Test getting info when no session exists."""
        response = client.get("/api/auth/session/info")

        assert response.status_code == 404

    def test_get_session_info_with_session(
        self, client: TestClient, mock_ksef_client, mock_crypto_service
    ):
        """Test getting info with active session."""
        # First init a session
        client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        # Then get info
        response = client.get("/api/auth/session/info")

        assert response.status_code == 200
        data = response.json()

        assert "referenceNumber" in data
        assert "nip" in data
        assert "createdAt" in data
