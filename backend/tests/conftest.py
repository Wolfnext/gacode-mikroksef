"""Pytest configuration and fixtures."""

import os
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import httpx
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ["KSEF_ENVIRONMENT"] = "test"
os.environ["COMPANY_NIP"] = "1234567890"
os.environ["KSEF_AUTH_TOKEN"] = "test-token"
os.environ["DATABASE_URL"] = "sqlite:///./test_mikroksef.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DEBUG"] = "true"

from app.main import app
from app.services.ksef_client import ksef_client
from app.services.session_manager import session_manager
from app.services.database import init_database, close_database


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create async test client."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def setup_database():
    """Initialize test database before each test."""
    await init_database()
    yield
    await close_database()
    # Clean up test database
    if os.path.exists("./test_mikroksef.db"):
        os.remove("./test_mikroksef.db")


@pytest.fixture
def mock_ksef_client(monkeypatch):
    """Mock KSeF client for isolated testing."""
    mock_client = AsyncMock()

    # Mock public key response
    mock_client.get_public_keys.return_value = {
        "publicKey": """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z3US
-----END PUBLIC KEY-----"""
    }

    # Mock session init response
    mock_client.init_token_session.return_value = {
        "sessionToken": {"token": "test-session-token"},
        "referenceNumber": "20260203-TEST-REF-001",
        "timestamp": "2026-02-03T10:00:00Z",
    }

    # Mock session status response
    mock_client.get_session_status.return_value = {
        "referenceNumber": "20260203-TEST-REF-001",
        "processingCode": 200,
        "processingDescription": "Active",
        "numberOfElements": 5,
        "timestamp": "2026-02-03T10:00:00Z",
    }

    # Mock terminate session
    mock_client.terminate_session.return_value = {
        "timestamp": "2026-02-03T10:30:00Z"
    }

    # Mock invoice query response
    mock_client.query_invoices.return_value = {
        "referenceNumber": "20260203-QUERY-001",
        "numberOfElements": 2,
        "pageSize": 50,
        "pageOffset": 0,
        "invoiceHeaderList": [
            {
                "invoiceReferenceNumber": "FV/2026/001",
                "ksefReferenceNumber": "1234567890-20260203-ABC123-XY",
                "invoicingDate": "2026-02-01",
                "acquisitionTimestamp": "2026-02-01T12:00:00Z",
                "subjectBy": {
                    "issuedByIdentifier": {"type": "nip", "identifier": "1234567890"},
                    "issuedByName": {"fullName": "Test Company Sp. z o.o."},
                },
                "subjectTo": {
                    "issuedToIdentifier": {"type": "nip", "identifier": "0987654321"},
                    "issuedToName": {"fullName": "Client Company S.A."},
                },
                "net": "1000.00",
                "vat": "230.00",
                "gross": "1230.00",
                "invoiceType": "VAT",
            },
            {
                "invoiceReferenceNumber": "FV/2026/002",
                "ksefReferenceNumber": "1234567890-20260203-DEF456-ZW",
                "invoicingDate": "2026-02-02",
                "acquisitionTimestamp": "2026-02-02T14:00:00Z",
                "subjectBy": {
                    "issuedByIdentifier": {"type": "nip", "identifier": "1234567890"},
                    "issuedByName": {"fullName": "Test Company Sp. z o.o."},
                },
                "subjectTo": {
                    "issuedToIdentifier": {"type": "nip", "identifier": "5555555555"},
                    "issuedToName": {"fullName": "Another Client Sp. z o.o."},
                },
                "net": "5000.00",
                "vat": "1150.00",
                "gross": "6150.00",
                "invoiceType": "VAT",
            },
        ],
    }

    # Mock invoice download
    mock_client.get_invoice.return_value = b"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="http://crd.gov.pl/wzor/2023/06/29/12648/">
    <Naglowek>
        <KodFormularza>FA</KodFormularza>
    </Naglowek>
</Faktura>"""

    monkeypatch.setattr("app.services.ksef_client.ksef_client", mock_client)
    return mock_client


@pytest.fixture
def mock_crypto_service(monkeypatch):
    """Mock crypto service for testing."""
    mock_crypto = MagicMock()
    mock_crypto.has_public_key = True
    mock_crypto.encrypt_token.return_value = "encrypted-token-base64"
    mock_crypto.encrypt_invoice.return_value = b"encrypted-invoice-bytes"
    mock_crypto.compute_sha256.return_value = "sha256-hash-base64"

    monkeypatch.setattr("app.services.crypto_service.crypto_service", mock_crypto)
    return mock_crypto


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing."""
    return {
        "ksef_reference_number": "1234567890-20260203-ABC123-XY",
        "invoice_reference_number": "FV/2026/001",
        "invoicing_date": "2026-02-01",
        "acquisition_timestamp": "2026-02-01T12:00:00Z",
        "subject_by_nip": "1234567890",
        "subject_by_name": "Test Company Sp. z o.o.",
        "subject_to_nip": "0987654321",
        "subject_to_name": "Client Company S.A.",
        "net_amount": 1000.00,
        "vat_amount": 230.00,
        "gross_amount": 1230.00,
        "currency": "PLN",
        "invoice_type": "VAT",
        "is_issued": True,
    }
