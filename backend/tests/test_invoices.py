"""Tests for invoice endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.services import database as db


class TestInvoiceEndpoints:
    """Test invoice endpoints."""

    def test_list_invoices_no_session(self, client: TestClient):
        """Test listing invoices without session (uses cache)."""
        response = client.get("/api/invoices")

        # Should work with cache (returns empty list)
        assert response.status_code == 200
        data = response.json()

        assert "invoiceHeaderList" in data
        assert data["numberOfElements"] == 0

    @pytest.mark.asyncio
    async def test_list_invoices_with_cache(
        self, client: TestClient, sample_invoice_data
    ):
        """Test listing invoices from cache."""
        # Add invoice to cache
        await db.save_invoice(sample_invoice_data)

        # List invoices
        response = client.get("/api/invoices")

        assert response.status_code == 200
        data = response.json()

        assert data["numberOfElements"] == 1
        assert len(data["invoiceHeaderList"]) == 1
        assert data["invoiceHeaderList"][0]["ksefReferenceNumber"] == sample_invoice_data["ksef_reference_number"]

    @pytest.mark.asyncio
    async def test_list_invoices_with_filters(
        self, client: TestClient, sample_invoice_data
    ):
        """Test listing invoices with date filters."""
        # Add invoice to cache
        await db.save_invoice(sample_invoice_data)

        # List with date filter
        response = client.get("/api/invoices?dateFrom=2026-01-01&dateTo=2026-12-31")

        assert response.status_code == 200
        data = response.json()

        assert data["numberOfElements"] == 1

    def test_list_invoices_from_ksef_no_session(self, client: TestClient):
        """Test listing from KSeF without session."""
        response = client.get("/api/invoices?useCache=false")

        assert response.status_code == 401
        assert "No active KSeF session" in response.json()["detail"]

    def test_list_invoices_from_ksef_with_session(
        self, client: TestClient, mock_ksef_client, mock_crypto_service
    ):
        """Test listing invoices directly from KSeF."""
        # Init session first
        client.post(
            "/api/auth/session/init-token",
            json={"nip": "1234567890"}
        )

        # List from KSeF
        response = client.get("/api/invoices?useCache=false")

        assert response.status_code == 200
        data = response.json()

        assert data["numberOfElements"] == 2
        assert len(data["invoiceHeaderList"]) == 2

    @pytest.mark.asyncio
    async def test_get_invoice_detail_from_cache(
        self, client: TestClient, sample_invoice_data
    ):
        """Test getting invoice detail from cache."""
        # Add invoice with XML content
        sample_invoice_data["xml_content"] = "<Invoice>Test</Invoice>"
        await db.save_invoice(sample_invoice_data)

        # Get detail
        ksef_ref = sample_invoice_data["ksef_reference_number"]
        response = client.get(f"/api/invoices/{ksef_ref}")

        assert response.status_code == 200
        data = response.json()

        assert data["header"]["ksefReferenceNumber"] == ksef_ref
        assert data["xmlContent"] == "<Invoice>Test</Invoice>"

    def test_get_invoice_detail_not_found(self, client: TestClient):
        """Test getting non-existent invoice."""
        response = client.get("/api/invoices/nonexistent-ref")

        assert response.status_code == 404

    def test_download_invoice_no_session_no_cache(self, client: TestClient):
        """Test downloading invoice without session and not in cache."""
        response = client.get("/api/invoices/some-ref/download")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_download_invoice_from_cache(
        self, client: TestClient, sample_invoice_data
    ):
        """Test downloading invoice from cache."""
        # Add invoice with XML
        sample_invoice_data["xml_content"] = "<?xml version='1.0'?><Invoice/>"
        await db.save_invoice(sample_invoice_data)

        ksef_ref = sample_invoice_data["ksef_reference_number"]
        response = client.get(f"/api/invoices/{ksef_ref}/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert ksef_ref in response.headers["content-disposition"]

    def test_get_invoice_status_no_session(self, client: TestClient):
        """Test getting invoice status without session."""
        response = client.get("/api/invoices/some-ref/status")

        assert response.status_code == 401

    def test_pagination(self, client: TestClient):
        """Test pagination parameters."""
        response = client.get("/api/invoices?pageSize=10&pageOffset=0")

        assert response.status_code == 200
        data = response.json()

        assert data["pageSize"] == 10
        assert data["pageOffset"] == 0

    def test_subject_type_filter(self, client: TestClient):
        """Test subject type filter."""
        # Test issued
        response = client.get("/api/invoices?subjectType=subject1")
        assert response.status_code == 200

        # Test received
        response = client.get("/api/invoices?subjectType=subject2")
        assert response.status_code == 200
