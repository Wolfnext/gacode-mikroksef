"""
Integration test for bulk invoice sending - 100 invoices to KSeF test environment.

This test uses REAL credentials from .env and sends to the actual KSeF test API.
Run with: pytest tests/test_bulk_invoices.py -v -s
"""

import asyncio
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.services.ksef_client import KSeFClient
from app.services.crypto_service import crypto_service
from app.services.session_manager import session_manager


def generate_invoice_xml(
    invoice_number: str,
    seller_nip: str,
    buyer_nip: str = "0987654321",
    issue_date: str = None,
    net_amount: str = "1000.00",
    vat_amount: str = "230.00",
    gross_amount: str = "1230.00",
) -> bytes:
    """Generate a minimal valid FA(2) invoice XML for KSeF."""
    if issue_date is None:
        issue_date = datetime.now().strftime("%Y-%m-%d")

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Faktura xmlns="http://crd.gov.pl/wzor/2023/06/29/12648/">
    <Naglowek>
        <KodFormularza kodSystemowy="FA (2)" wersjaSchemy="1-0E">FA</KodFormularza>
        <WariantFormularza>2</WariantFormularza>
        <DataWytworzeniaFa>{timestamp}</DataWytworzeniaFa>
        <SystemInfo>mikroKSeF-bulk-test</SystemInfo>
    </Naglowek>
    <Podmiot1>
        <DaneIdentyfikacyjne>
            <NIP>{seller_nip}</NIP>
            <Nazwa>Test Seller Company Sp. z o.o.</Nazwa>
        </DaneIdentyfikacyjne>
        <Adres>
            <KodKraju>PL</KodKraju>
            <AdresL1>ul. Testowa 123</AdresL1>
            <AdresL2>00-001 Warszawa</AdresL2>
        </Adres>
    </Podmiot1>
    <Podmiot2>
        <DaneIdentyfikacyjne>
            <NIP>{buyer_nip}</NIP>
            <Nazwa>Test Buyer Company S.A.</Nazwa>
        </DaneIdentyfikacyjne>
        <Adres>
            <KodKraju>PL</KodKraju>
            <AdresL1>ul. Kupiecka 456</AdresL1>
            <AdresL2>00-002 Kraków</AdresL2>
        </Adres>
    </Podmiot2>
    <Fa>
        <KodWaluty>PLN</KodWaluty>
        <P_1>{issue_date}</P_1>
        <P_2>{invoice_number}</P_2>
        <P_13_1>{net_amount}</P_13_1>
        <P_14_1>{vat_amount}</P_14_1>
        <P_15>{gross_amount}</P_15>
        <Adnotacje>
            <P_16>2</P_16>
            <P_17>2</P_17>
            <P_18>2</P_18>
            <P_18A>2</P_18A>
            <Zwolnienie>
                <P_19N>1</P_19N>
            </Zwolnienie>
            <NoweSrodkiTransportu>
                <P_22N>1</P_22N>
            </NoweSrodkiTransportu>
            <P_23>2</P_23>
            <PMarzy>
                <P_PMarzyN>1</P_PMarzyN>
            </PMarzy>
        </Adnotacje>
        <FaWiersz>
            <NrWierszaFa>1</NrWierszaFa>
            <P_7>Test Product / Service - Bulk Test</P_7>
            <P_8A>szt.</P_8A>
            <P_8B>1</P_8B>
            <P_9A>{net_amount}</P_9A>
            <P_11>{net_amount}</P_11>
            <P_12>23</P_12>
        </FaWiersz>
    </Fa>
</Faktura>"""
    return xml.encode("utf-8")


class TestBulkInvoiceIntegration:
    """Integration tests that send real invoices to KSeF test environment."""

    @pytest.fixture
    def settings(self):
        """Get application settings."""
        return get_settings()

    @pytest.fixture
    async def ksef_client(self):
        """Create KSeF client."""
        client = KSeFClient()
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_send_100_invoices_real(self, settings, ksef_client):
        """
        REAL TEST: Send 100 invoices to KSeF test environment.

        Requirements:
        - Valid COMPANY_NIP in .env
        - Valid KSEF_AUTH_TOKEN in .env
        - KSEF_ENVIRONMENT=test in .env
        """
        nip = settings.company_nip
        token = settings.ksef_auth_token

        if not nip or nip == "1234567890":
            pytest.skip("Set real COMPANY_NIP in .env")
        if not token or token == "your_authorization_token_here":
            pytest.skip("Set real KSEF_AUTH_TOKEN in .env")

        print(f"\n{'='*60}")
        print(f"BULK INVOICE TEST - 100 INVOICES")
        print(f"{'='*60}")
        print(f"Environment: {settings.ksef_environment}")
        print(f"NIP: {nip}")
        print(f"API URL: {ksef_client.base_url}")
        print(f"{'='*60}\n")

        # Step 1: Get challenge and init session
        print("[1/5] Getting auth challenge...")
        challenge_response = await ksef_client.get_auth_challenge()
        challenge = challenge_response.get("challenge")
        print(f"      Challenge: {challenge[:20]}...")

        # Step 2: Encrypt token and init session
        print("[2/5] Initializing token session...")

        # Load public key if not already loaded
        if not crypto_service.has_public_key:
            keys = await ksef_client.get_public_keys()
            if keys and len(keys) > 0:
                # v2 API returns list of certificates with base64-encoded DER
                first_key = keys[0]
                cert_data = first_key.get("publicKeyCertificate") or first_key.get("certificate")
                if cert_data:
                    crypto_service.set_ministry_public_key_from_der(cert_data)
                else:
                    # Fallback to PEM if available
                    pem = first_key.get("publicKey") or str(first_key)
                    crypto_service.set_ministry_public_key(pem)

        # v2 API: encrypt "token|timestamp"
        import time
        timestamp_ms = int(time.time() * 1000)
        token_with_timestamp = f"{token}|{timestamp_ms}"
        encrypted_token = crypto_service.encrypt_token_v2(token_with_timestamp)

        init_response = await ksef_client.init_token_session(
            challenge=challenge,
            nip=nip,
            encrypted_token=encrypted_token,
        )

        reference_number = init_response.get("referenceNumber")
        print(f"      Session ref: {reference_number}")

        # Get authenticationToken from init response
        auth_token = init_response.get("authenticationToken", {}).get("token")
        if not auth_token:
            raise Exception("No authenticationToken in init response")
        print(f"      Got auth token: {auth_token[:50]}...")

        # Wait for authentication to be processed
        print("[3/5] Waiting for authentication to complete...")
        access_token = None
        for attempt in range(30):
            await asyncio.sleep(1)
            try:
                # Try to redeem the token
                redeem_response = await ksef_client.redeem_token(auth_token)
                print(f"      Redeem response: {redeem_response}")
                access_token = redeem_response.get("accessToken")
                if access_token:
                    print(f"      Got access token!")
                    break
            except Exception as e:
                error_msg = str(e)
                if "400" in error_msg or "Brak autoryzacji" in error_msg:
                    print(f"      Still processing... (attempt {attempt + 1})")
                else:
                    print(f"      Error: {error_msg}")
                    raise

        if not access_token:
            raise Exception("Failed to get access token")

        # Create online session
        print("[4/5] Creating online session...")
        session_response = await ksef_client.create_online_session(access_token)
        session_ref = session_response.get("referenceNumber")
        print(f"      Online session: {session_ref}")

        # Send 100 invoices
        print(f"\n{'='*60}")
        print("SENDING 100 INVOICES...")
        print(f"{'='*60}\n")

        results = []
        errors = []
        invoice_count = 100

        for i in range(1, invoice_count + 1):
            invoice_number = f"BULK-TEST/{datetime.now().strftime('%Y%m%d')}/{i:04d}"
            net = Decimal("100.00") + Decimal(i)
            vat = (net * Decimal("0.23")).quantize(Decimal("0.01"))
            gross = net + vat

            invoice_xml = generate_invoice_xml(
                invoice_number=invoice_number,
                seller_nip=nip,
                net_amount=str(net),
                vat_amount=str(vat),
                gross_amount=str(gross),
            )

            try:
                result = await ksef_client.send_invoice(
                    access_token,
                    session_ref,
                    invoice_xml,
                )
                results.append({
                    "invoice_number": invoice_number,
                    "ksef_ref": result.get("ksefReferenceNumber"),
                    "status": result.get("processingCode"),
                })

                if i % 10 == 0:
                    print(f"  [{i:3d}/100] Sent {invoice_number} -> {result.get('ksefReferenceNumber', 'pending')}")

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)

            except Exception as e:
                errors.append({
                    "invoice_number": invoice_number,
                    "error": str(e),
                })
                print(f"  [{i:3d}/100] ERROR: {invoice_number} -> {e}")

        # Close session
        print(f"\n{'='*60}")
        print("CLOSING SESSION...")
        try:
            await ksef_client.close_online_session(access_token, session_ref)
            print("Session closed successfully")
        except Exception as e:
            print(f"Warning: Could not close session: {e}")

        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total invoices: {invoice_count}")
        print(f"Successful: {len(results)}")
        print(f"Failed: {len(errors)}")

        if results:
            print(f"\nFirst invoice: {results[0]}")
            print(f"Last invoice: {results[-1]}")

        if errors:
            print(f"\nErrors:")
            for err in errors[:5]:  # Show first 5 errors
                print(f"  - {err}")

        # Assert
        assert len(results) >= 90, f"Expected at least 90 successful invoices, got {len(results)}"
        print(f"\n✓ TEST PASSED: {len(results)} invoices sent successfully!")


async def main():
    """Run the bulk invoice test directly."""
    # Load env from parent directory
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    settings = get_settings()
    client = KSeFClient()

    test = TestBulkInvoiceIntegration()
    try:
        await test.test_send_100_invoices_real(settings, client)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
