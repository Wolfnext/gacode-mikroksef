"""
KSeF API Client v2
HTTP client for communicating with the KSeF (Krajowy System e-Faktur) API v2.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx

from app.config import get_settings
from app.utils.exceptions import KSeFAPIError, KSeFAuthError, KSeFRateLimitError

logger = logging.getLogger(__name__)


class KSeFClient:
    """Async HTTP client for KSeF API v2 communication."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def base_url(self) -> str:
        """Get the base URL for KSeF API v2."""
        env = self.settings.ksef_environment
        v2_hosts = {
            "test": "https://api-test.ksef.mf.gov.pl/v2",
            "demo": "https://api-demo.ksef.mf.gov.pl/v2",
            "production": "https://api.ksef.mf.gov.pl/v2",
        }
        return v2_hosts.get(env, v2_hosts["test"])

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                headers={
                    "Accept": "application/json",
                    "User-Agent": f"mikroKSeF/{self.settings.app_name}",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_headers(self, auth_token: Optional[str] = None) -> Dict[str, str]:
        """Build request headers for KSeF v2 API."""
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response, raising appropriate errors."""
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            raise KSeFRateLimitError(
                f"Rate limit exceeded. Retry after {retry_after}s",
                retry_after=int(retry_after),
            )

        if response.status_code == 401:
            raise KSeFAuthError("Authentication failed or session expired")

        if response.status_code == 403:
            try:
                error_detail = response.json()
                logger.error(f"403 Forbidden details: {error_detail}")
            except Exception:
                logger.error(f"403 Forbidden body: {response.text}")
            raise KSeFAuthError("Access forbidden - insufficient permissions")

        if response.status_code >= 400:
            try:
                error_data = response.json()
                exc = error_data.get("exception", {})
                if isinstance(exc, dict):
                    details = exc.get("exceptionDetailList", [])
                    if details:
                        message = details[0].get("exceptionDescription", response.text)
                    else:
                        message = exc.get("exceptionDescription", response.text)
                else:
                    message = str(exc) or response.text
            except Exception:
                message = response.text
            raise KSeFAPIError(
                f"KSeF API error ({response.status_code}): {message}",
                status_code=response.status_code,
            )

        if response.status_code == 204:
            return {}

        return response.json()

    # ===== Authentication Endpoints =====

    async def get_auth_challenge(self) -> Dict[str, Any]:
        """
        POST /auth/challenge
        Get authorization challenge for session initialization.
        """
        logger.info("Getting auth challenge")
        response = await self.client.post("/auth/challenge", headers=self._get_headers())
        return await self._handle_response(response)

    async def init_token_session(
        self, challenge: str, nip: str, encrypted_token: str
    ) -> Dict[str, Any]:
        """
        POST /auth/ksef-token
        Initialize session with encrypted KSeF token.
        """
        logger.info(f"Initializing token session for NIP: {nip}")
        response = await self.client.post(
            "/auth/ksef-token",
            json={
                "challenge": challenge,
                "contextIdentifier": {"type": "Nip", "value": nip},
                "encryptedToken": encrypted_token,
            },
            headers=self._get_headers(),
        )
        return await self._handle_response(response)

    async def get_auth_status(self, auth_token: str, reference_number: str) -> Dict[str, Any]:
        """
        GET /auth/{referenceNumber}
        Check authentication process status.
        """
        logger.info(f"Checking auth status: {reference_number}")
        response = await self.client.get(
            f"/auth/{reference_number}",
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)

    async def redeem_token(self, auth_token: str) -> Dict[str, Any]:
        """
        POST /auth/token/redeem
        Exchange temporary authenticationToken for accessToken + refreshToken.
        Tokens can only be redeemed once.
        """
        logger.info("Redeeming authToken for accessToken via POST /auth/token/redeem")
        response = await self.client.post(
            "/auth/token/redeem",
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        POST /auth/token/refresh
        Refresh authentication token.
        """
        logger.info("Refreshing token")
        response = await self.client.post(
            "/auth/token/refresh",
            headers=self._get_headers(refresh_token),
        )
        return await self._handle_response(response)

    async def terminate_session(self, auth_token: str) -> Dict[str, Any]:
        """
        DELETE /auth/sessions/current
        Terminate current session.
        """
        logger.info("Terminating session")
        response = await self.client.delete(
            "/auth/sessions/current",
            headers=self._get_headers(auth_token),
        )
        if response.status_code == 204:
            return {}
        return await self._handle_response(response)

    # ===== Online Session Endpoints =====

    async def create_online_session(self, auth_token: str) -> Dict[str, Any]:
        """
        POST /sessions/online
        Create online session for invoice operations.
        """
        logger.info("Creating online session")
        response = await self.client.post(
            "/sessions/online",
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)

    async def get_session_status(self, auth_token: str, reference_number: str) -> Dict[str, Any]:
        """
        GET /sessions/{referenceNumber}
        Get session status.
        """
        response = await self.client.get(
            f"/sessions/{reference_number}",
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)

    async def close_online_session(self, auth_token: str, reference_number: str) -> Dict[str, Any]:
        """
        POST /sessions/online/{referenceNumber}/close
        Close online session.
        """
        logger.info(f"Closing online session: {reference_number}")
        response = await self.client.post(
            f"/sessions/online/{reference_number}/close",
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)

    async def get_session_invoices(
        self, auth_token: str, reference_number: str, page_size: int = 100
    ) -> Dict[str, Any]:
        """
        GET /sessions/{referenceNumber}/invoices
        Get invoices sent in session.
        """
        response = await self.client.get(
            f"/sessions/{reference_number}/invoices",
            params={"pageSize": page_size},
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)

    # ===== Invoice Endpoints =====

    async def query_invoices(
        self,
        auth_token: str,
        query_filters: Dict[str, Any],
        *,
        page_offset: Optional[int] = None,
        page_size: Optional[int] = None,
        sort_order: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        POST /invoices/query/metadata
        Query invoice metadata.
        """
        params: Dict[str, Any] = {}
        if page_offset is not None:
            params["pageOffset"] = page_offset
        if page_size is not None:
            params["pageSize"] = page_size
        if sort_order:
            params["sortOrder"] = sort_order

        logger.info(f"Querying invoices with filters: {query_filters} params={params or None}")
        response = await self.client.post(
            "/invoices/query/metadata",
            params=params or None,
            json=query_filters,
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)

    async def get_invoice(self, auth_token: str, ksef_number: str) -> bytes:
        """
        GET /invoices/ksef/{ksefNumber}
        Get invoice XML by KSeF number.
        Returns raw XML bytes.
        """
        logger.info(f"Getting invoice: {ksef_number}")
        headers = self._get_headers(auth_token)
        headers["Accept"] = "application/xml"
        response = await self.client.get(
            f"/invoices/ksef/{ksef_number}",
            headers=headers,
        )
        if response.status_code >= 400:
            await self._handle_response(response)
        return response.content

    async def request_invoice_export(
        self, auth_token: str, query_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        POST /invoices/exports
        Request invoice export (async).
        """
        logger.info("Requesting invoice export")
        response = await self.client.post(
            "/invoices/exports",
            json=query_params,
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)

    async def get_export_status(self, auth_token: str, reference_number: str) -> Dict[str, Any]:
        """
        GET /invoices/exports/{referenceNumber}
        Get export status and download URL.
        """
        response = await self.client.get(
            f"/invoices/exports/{reference_number}",
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)

    # ===== Send Invoice in Online Session =====

    async def send_invoice(
        self, auth_token: str, session_reference: str, invoice_xml: bytes
    ) -> Dict[str, Any]:
        """
        POST /sessions/online/{referenceNumber}/invoices
        Send invoice in online session.
        """
        logger.info(f"Sending invoice in session: {session_reference}")
        response = await self.client.post(
            f"/sessions/online/{session_reference}/invoices",
            content=invoice_xml,
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/octet-stream",
                "Accept": "application/json",
            },
        )
        return await self._handle_response(response)

    async def get_invoice_upo(
        self, auth_token: str, session_reference: str, invoice_reference: str
    ) -> bytes:
        """
        GET /sessions/{referenceNumber}/invoices/{invoiceReferenceNumber}/upo
        Get UPO for invoice.
        """
        response = await self.client.get(
            f"/sessions/{session_reference}/invoices/{invoice_reference}/upo",
            headers=self._get_headers(auth_token),
        )
        if response.status_code != 200:
            await self._handle_response(response)
        return response.content

    # ===== Public Endpoints =====

    async def get_public_keys(self) -> List[Dict[str, Any]]:
        """
        GET /security/public-key-certificates
        Get Ministry's public encryption keys (certificates).
        """
        logger.info("Fetching public keys")
        response = await self.client.get("/security/public-key-certificates")
        if response.status_code != 200:
            raise KSeFAPIError(f"Failed to fetch public keys: {response.status_code}")
        return response.json()

    async def get_rate_limits(self, auth_token: str) -> Dict[str, Any]:
        """
        GET /rate-limits
        Get current rate limit status.
        """
        response = await self.client.get(
            "/rate-limits",
            headers=self._get_headers(auth_token),
        )
        return await self._handle_response(response)


# Singleton instance
ksef_client = KSeFClient()
