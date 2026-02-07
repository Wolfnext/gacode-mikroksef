"""Extract searchable text from KSeF invoice XML."""

import logging
from lxml import etree

logger = logging.getLogger(__name__)

# Known KSeF FA namespaces
_NAMESPACES = [
    {"fa": "http://crd.gov.pl/wzor/2023/06/29/12648/"},  # FA(3)
    {"fa": "http://crd.gov.pl/wzor/2022/01/13/11673/"},  # FA(2)
    {"fa": "http://crd.gov.pl/wzor/2021/11/29/11089/"},  # FA(1)
]

_XPATH_QUERIES = [
    "//fa:P_7/text()",        # Item name
    "//fa:P_12Nazwa/text()",  # Item description
    "//fa:KodCN/text()",      # CN code
    "//fa:PKWIU/text()",      # PKWiU code
    "//fa:GTIN/text()",       # GTIN code
    "//fa:Adnotacje//text()", # Annotations
    "//fa:DodatkowyOpis/text()",  # Additional description
]


def extract_searchable_text(xml_content: str) -> str:
    """Extract searchable text fields from KSeF invoice XML."""
    if not xml_content:
        return ""

    try:
        root = etree.fromstring(
            xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content
        )
    except Exception as e:
        logger.warning(f"Failed to parse XML for search indexing: {e}")
        return ""

    parts: list[str] = []

    for ns in _NAMESPACES:
        for xpath in _XPATH_QUERIES:
            try:
                results = root.xpath(xpath, namespaces=ns)
                for text in results:
                    stripped = str(text).strip()
                    if stripped:
                        parts.append(stripped)
            except Exception:
                continue

        if parts:
            break  # Found content with this namespace, stop trying others

    return " ".join(parts)
