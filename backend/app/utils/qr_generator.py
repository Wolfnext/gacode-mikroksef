"""QR code URL generation for KSeF invoice verification."""


def generate_ksef_qr_url(ksef_reference_number: str, environment: str = "test") -> str:
    """Generate KSeF verification URL for QR code embedding in PDF."""
    base_urls = {
        "test": "https://ksef-test.mf.gov.pl",
        "demo": "https://ksef-demo.mf.gov.pl",
        "production": "https://ksef.mf.gov.pl",
    }
    base_url = base_urls.get(environment, base_urls["test"])
    return f"{base_url}/web/verify/{ksef_reference_number}"
