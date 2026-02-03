"""
Session Manager
Manages KSeF API v2 sessions including token storage and refresh.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.config import get_settings
from app.services.ksef_client import ksef_client
from app.services.crypto_service import crypto_service
from app.utils.exceptions import KSeFAuthError, KSeFSessionError

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """Represents an active KSeF session."""

    token: str
    reference_number: str
    nip: str
    created_at: datetime
    expires_at: datetime
    processing_code: int = 200
    invoice_count: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if session is valid and not expired."""
        return not self.is_expired and self.processing_code == 200

    @property
    def time_remaining(self) -> timedelta:
        """Get remaining session time."""
        remaining = self.expires_at - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            "referenceNumber": self.reference_number,
            "nip": self.nip,
            "createdAt": self.created_at.isoformat(),
            "expiresAt": self.expires_at.isoformat(),
            "isExpired": self.is_expired,
            "processingCode": self.processing_code,
            "invoiceCount": self.invoice_count,
        }


class SessionManager:
    """Manages KSeF API v2 sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}
        self._current_session: Optional[Session] = None
        self._current_nip: Optional[str] = None

    @property
    def current_session(self) -> Optional[Session]:
        """Get current active session if valid."""
        if self._current_session and self._current_session.is_valid:
            return self._current_session
        return None

    @property
    def session_token(self) -> Optional[str]:
        """Get current session token."""
        session = self.current_session
        return session.token if session else None

    @property
    def has_active_session(self) -> bool:
        """Check if there's an active session."""
        return self.current_session is not None

    async def _ensure_public_key(self) -> None:
        """Ensure Ministry public key is loaded."""
        if crypto_service.has_public_key:
            return

        logger.info("Fetching Ministry public key")
        try:
            keys_response = await ksef_client.get_public_keys()

            # v2 API returns a list of certificates
            if isinstance(keys_response, list):
                # Find certificate for token encryption
                token_cert = None
                for cert in keys_response:
                    usage = cert.get("usage", [])
                    if "KsefTokenEncryption" in usage:
                        token_cert = cert
                        break

                if not token_cert:
                    # Fall back to first certificate
                    token_cert = keys_response[0] if keys_response else None

                if not token_cert:
                    raise KSeFAuthError("No certificates in response")

                # Load DER certificate (base64 encoded)
                cert_base64 = token_cert.get("certificate")
                if not cert_base64:
                    raise KSeFAuthError("Certificate data missing")

                crypto_service.set_ministry_public_key_from_der(cert_base64)
                logger.info(f"Loaded certificate valid until: {token_cert.get('validTo')}")
            else:
                raise KSeFAuthError("Invalid public key response format")

        except KSeFAuthError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch public key: {e}")
            raise KSeFAuthError(f"Cannot fetch Ministry public key: {e}")

    async def init_session_with_token(self, nip: str, auth_token: Optional[str] = None) -> Session:
        """
        Initialize KSeF session using encrypted token authentication (v2 API).

        v2 API flow:
        1. POST /auth/challenge -> get challenge + timestampMs
        2. Encrypt "token|timestampMs" with RSA-OAEP SHA-256
        3. POST /auth/ksef-token with challenge, nip, encryptedToken

        Args:
            nip: Company NIP
            auth_token: Authorization token (uses config if not provided)

        Returns:
            Active session object
        """
        settings = get_settings()

        # Use provided token or fall back to config
        token = auth_token or settings.ksef_auth_token
        if not token:
            raise KSeFAuthError("No authorization token configured")

        logger.info(f"Initializing session for NIP: {nip}")

        # Ensure we have the public key
        await self._ensure_public_key()

        # Step 1: Get challenge
        try:
            challenge_response = await ksef_client.get_auth_challenge()
            challenge = challenge_response.get("challenge")
            timestamp_ms = challenge_response.get("timestampMs")

            if not challenge or not timestamp_ms:
                raise KSeFAuthError("Invalid challenge response")

            logger.info(f"Got challenge: {challenge}")
        except Exception as e:
            logger.error(f"Failed to get challenge: {e}")
            raise KSeFSessionError(f"Failed to get challenge: {e}")

        # Step 2: Encrypt token|timestamp with RSA-OAEP
        token_with_timestamp = f"{token}|{timestamp_ms}"
        encrypted_token = crypto_service.encrypt_token_v2(token_with_timestamp)

        # Step 3: Initialize session with KSeF
        try:
            response = await ksef_client.init_token_session(
                challenge=challenge,
                nip=nip,
                encrypted_token=encrypted_token,
            )
        except Exception as e:
            logger.error(f"Session init failed: {e}")
            raise KSeFSessionError(f"Failed to initialize session: {e}")

        # Extract session data from v2 response
        logger.info(f"Token session response: {response}")
        reference_number = response.get("referenceNumber", "")
        auth_token_data = response.get("authenticationToken", {})

        if isinstance(auth_token_data, dict):
            temp_token = auth_token_data.get("token", "")
            valid_until = auth_token_data.get("validUntil", "")
            logger.info(f"Extracted temp token (first 20 chars): {temp_token[:20] if temp_token else 'EMPTY'}...")
        else:
            temp_token = str(auth_token_data)
            valid_until = ""
            logger.info(f"Temp token as string (first 20 chars): {temp_token[:20] if temp_token else 'EMPTY'}...")

        # Step 4: Check auth status and wait for completion
        import asyncio
        token_value = temp_token
        for attempt in range(5):
            try:
                status_response = await ksef_client.get_auth_status(temp_token, reference_number)
                logger.info(f"Auth status: {status_response}")
                status_code = status_response.get("status", {}).get("code", 0)
                if status_code == 200:  # Auth completed successfully
                    logger.info("Authentication completed successfully")
                    break
                elif status_code == 100:  # Still processing
                    logger.info("Auth still processing, waiting...")
                    await asyncio.sleep(1)
                else:
                    logger.warning(f"Auth status code: {status_code}")
                    break
            except Exception as e:
                logger.warning(f"Auth status check failed: {e}")
                break

        # Step 5: Redeem temporary token for accessToken
        try:
            redeem_response = await ksef_client.redeem_token(temp_token)
            logger.info(f"Redeem response: {redeem_response}")

            access_token_data = redeem_response.get("accessToken", {})
            if isinstance(access_token_data, dict):
                token_value = access_token_data.get("token", temp_token)
                valid_until = access_token_data.get("validUntil", valid_until)
            else:
                token_value = str(access_token_data) if access_token_data else temp_token

            logger.info(f"Got accessToken (first 20 chars): {token_value[:20] if token_value else 'EMPTY'}...")
        except Exception as e:
            logger.warning(f"Token redeem failed, using temp token: {e}")
            token_value = temp_token

        created_at = datetime.utcnow()

        # Parse expiration time
        if valid_until:
            try:
                expires_at = datetime.fromisoformat(valid_until.replace("Z", "+00:00").replace("+00:00", ""))
            except Exception:
                expires_at = created_at + timedelta(minutes=settings.session_timeout_minutes)
        else:
            expires_at = created_at + timedelta(minutes=settings.session_timeout_minutes)

        # Step 5: Create online session for invoice operations
        try:
            online_response = await ksef_client.create_online_session(token_value)
            online_reference = online_response.get("referenceNumber", reference_number)
            logger.info(f"Online session created: {online_reference}")
        except Exception as e:
            logger.warning(f"Online session creation failed (continuing): {e}")
            online_reference = reference_number

        # Create session object
        session = Session(
            token=token_value,
            reference_number=online_reference,
            nip=nip,
            created_at=created_at,
            expires_at=expires_at,
        )

        # Store session
        self._sessions[online_reference] = session
        self._current_session = session
        self._current_nip = nip

        logger.info(f"Session initialized: {online_reference}")
        return session

    async def get_status(self) -> Optional[Dict]:
        """Get current session status - returns local session info.

        Note: v2 API session status endpoint often returns 403, so we rely on
        local session state instead of querying the API repeatedly.
        """
        if not self.current_session:
            return None

        # Return local session info instead of querying API
        # This avoids repeated 403 errors from v2 API
        return self.current_session.to_dict()

    async def terminate(self) -> bool:
        """Terminate current session."""
        if not self.current_session:
            return False

        try:
            await ksef_client.terminate_session(
                self.session_token,
            )
            logger.info(f"Session terminated: {self._current_session.reference_number}")
        except Exception as e:
            logger.warning(f"Session termination error: {e}")

        # Clear session regardless of KSeF response
        if self._current_session:
            ref = self._current_session.reference_number
            if ref in self._sessions:
                del self._sessions[ref]
        self._current_session = None
        self._current_nip = None

        return True

    async def close_all_sessions(self) -> None:
        """Terminate all active sessions (cleanup)."""
        logger.info("Closing all sessions")

        for session in list(self._sessions.values()):
            if session.is_valid:
                try:
                    await ksef_client.terminate_session(
                        session.token,
                    )
                except Exception as e:
                    logger.warning(f"Failed to terminate session {session.reference_number}: {e}")

        self._sessions.clear()
        self._current_session = None
        self._current_nip = None

    def require_session(self) -> str:
        """
        Get session token or raise error if no active session.

        Returns:
            Active session token

        Raises:
            KSeFSessionError: If no active session
        """
        token = self.session_token
        if not token:
            raise KSeFSessionError("No active KSeF session. Please authenticate first.")
        return token

    def get_session_info(self) -> Optional[Dict]:
        """Get information about current session."""
        session = self.current_session
        if not session:
            return None
        return session.to_dict()


# Singleton instance
session_manager = SessionManager()
