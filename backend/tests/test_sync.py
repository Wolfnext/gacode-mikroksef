"""Tests for sync endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestSyncEndpoints:
    """Test sync endpoints."""

    def test_sync_no_session(self, client: TestClient):
        """Test sync without active session."""
        response = client.post(
            "/api/sync",
            json={"subjectType": "subject1"}
        )

        assert response.status_code == 401
        assert "No active KSeF session" in response.json()["detail"]

    def test_sync_issued_no_session(self, client: TestClient):
        """Test sync issued invoices without session."""
        response = client.post("/api/sync/issued")

        assert response.status_code == 401

    def test_sync_received_no_session(self, client: TestClient):
        """Test sync received invoices without session."""
        response = client.post("/api/sync/received")

        assert response.status_code == 401

    def test_sync_status_never_synced(self, client: TestClient):
        """Test sync status when never synced."""
        response = client.get("/api/sync/status")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "never_synced"

    def test_sync_with_session(
        self, client: TestClient, mock_ksef_client, mock_crypto_service
    ):
        """Test sync with active session."""
        # Init session
        client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        # Sync
        response = client.post(
            "/api/sync",
            json={"subjectType": "subject1"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["completed", "running"]
        assert "totalFetched" in data
        assert "newInvoices" in data

    def test_sync_issued_with_session(
        self, client: TestClient, mock_ksef_client, mock_crypto_service
    ):
        """Test sync issued invoices with session."""
        # Init session
        client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        # Sync issued
        response = client.post("/api/sync/issued")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["totalFetched"] == 2  # From mock

    def test_sync_received_with_session(
        self, client: TestClient, mock_ksef_client, mock_crypto_service
    ):
        """Test sync received invoices with session."""
        # Init session
        client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        # Sync received
        response = client.post("/api/sync/received")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"

    def test_clear_cache(self, client: TestClient):
        """Test clearing invoice cache."""
        response = client.delete("/api/sync/cache")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "deletedCount" in data

    def test_sync_with_date_filters(
        self, client: TestClient, mock_ksef_client, mock_crypto_service
    ):
        """Test sync with date filters."""
        # Init session
        client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        # Sync with date filters
        response = client.post("/api/sync/issued?dateFrom=2026-01-01&dateTo=2026-12-31")

        assert response.status_code == 200

    def test_full_sync(
        self, client: TestClient, mock_ksef_client, mock_crypto_service
    ):
        """Test full sync (clear cache first)."""
        # Init session
        client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        # Full sync
        response = client.post("/api/sync/issued?fullSync=true")

        assert response.status_code == 200
