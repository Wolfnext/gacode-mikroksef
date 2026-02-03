"""
Database Service
SQLite database for local invoice caching and session persistence.
"""

import logging
import aiosqlite
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

# Global database connection
_db: Optional[aiosqlite.Connection] = None


async def init_database() -> None:
    """Initialize database and create tables."""
    global _db

    settings = get_settings()
    db_path = settings.database_url.replace("sqlite:///", "")

    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing database: {db_path}")

    _db = await aiosqlite.connect(db_path)
    _db.row_factory = aiosqlite.Row

    # Create tables
    await _db.executescript("""
        -- Invoice cache table
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ksef_reference_number TEXT UNIQUE NOT NULL,
            invoice_reference_number TEXT,
            invoicing_date DATE,
            acquisition_timestamp DATETIME,
            subject_by_nip TEXT,
            subject_by_name TEXT,
            subject_to_nip TEXT,
            subject_to_name TEXT,
            net_amount DECIMAL(15,2),
            vat_amount DECIMAL(15,2),
            gross_amount DECIMAL(15,2),
            currency TEXT DEFAULT 'PLN',
            invoice_type TEXT,
            schema_version TEXT,
            hash_value TEXT,
            xml_content TEXT,
            is_issued BOOLEAN DEFAULT 1,
            upo_reference TEXT,
            cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Index for faster queries
        CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoicing_date);
        CREATE INDEX IF NOT EXISTS idx_invoices_subject_by ON invoices(subject_by_nip);
        CREATE INDEX IF NOT EXISTS idx_invoices_subject_to ON invoices(subject_to_nip);
        CREATE INDEX IF NOT EXISTS idx_invoices_acquisition ON invoices(acquisition_timestamp);
        CREATE INDEX IF NOT EXISTS idx_invoices_is_issued ON invoices(is_issued);

        -- Sync status table
        CREATE TABLE IF NOT EXISTS sync_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_type TEXT NOT NULL,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            status TEXT DEFAULT 'running',
            total_fetched INTEGER DEFAULT 0,
            new_invoices INTEGER DEFAULT 0,
            updated_invoices INTEGER DEFAULT 0,
            errors TEXT,
            last_acquisition_timestamp DATETIME
        );

        -- Sessions table (for persistence)
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_number TEXT UNIQUE NOT NULL,
            nip TEXT NOT NULL,
            token_hash TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            is_active BOOLEAN DEFAULT 1
        );
    """)

    await _db.commit()
    logger.info("Database initialized successfully")


async def close_database() -> None:
    """Close database connection."""
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("Database connection closed")


async def get_db() -> aiosqlite.Connection:
    """Get database connection."""
    if _db is None:
        await init_database()
    return _db


# ===== Invoice Operations =====

def _to_float(value: Any) -> Optional[float]:
    """Convert Decimal or numeric value to float for SQLite."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def save_invoice(invoice_data: Dict[str, Any]) -> int:
    """
    Save or update invoice in cache.

    Returns:
        Invoice ID
    """
    db = await get_db()

    # Convert Decimal values to float for SQLite compatibility
    net_amount = _to_float(invoice_data.get("net_amount"))
    vat_amount = _to_float(invoice_data.get("vat_amount"))
    gross_amount = _to_float(invoice_data.get("gross_amount"))

    # Check if exists
    cursor = await db.execute(
        "SELECT id FROM invoices WHERE ksef_reference_number = ?",
        (invoice_data.get("ksef_reference_number"),)
    )
    existing = await cursor.fetchone()

    if existing:
        # Update existing
        await db.execute("""
            UPDATE invoices SET
                invoice_reference_number = ?,
                invoicing_date = ?,
                acquisition_timestamp = ?,
                subject_by_nip = ?,
                subject_by_name = ?,
                subject_to_nip = ?,
                subject_to_name = ?,
                net_amount = ?,
                vat_amount = ?,
                gross_amount = ?,
                currency = ?,
                invoice_type = ?,
                schema_version = ?,
                hash_value = ?,
                xml_content = COALESCE(?, xml_content),
                is_issued = ?,
                upo_reference = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE ksef_reference_number = ?
        """, (
            invoice_data.get("invoice_reference_number"),
            invoice_data.get("invoicing_date"),
            invoice_data.get("acquisition_timestamp"),
            invoice_data.get("subject_by_nip"),
            invoice_data.get("subject_by_name"),
            invoice_data.get("subject_to_nip"),
            invoice_data.get("subject_to_name"),
            net_amount,
            vat_amount,
            gross_amount,
            invoice_data.get("currency", "PLN"),
            invoice_data.get("invoice_type"),
            invoice_data.get("schema_version"),
            invoice_data.get("hash_value"),
            invoice_data.get("xml_content"),
            invoice_data.get("is_issued", True),
            invoice_data.get("upo_reference"),
            invoice_data.get("ksef_reference_number"),
        ))
        await db.commit()
        return existing["id"]
    else:
        # Insert new
        cursor = await db.execute("""
            INSERT INTO invoices (
                ksef_reference_number, invoice_reference_number, invoicing_date,
                acquisition_timestamp, subject_by_nip, subject_by_name,
                subject_to_nip, subject_to_name, net_amount, vat_amount,
                gross_amount, currency, invoice_type, schema_version,
                hash_value, xml_content, is_issued, upo_reference
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_data.get("ksef_reference_number"),
            invoice_data.get("invoice_reference_number"),
            invoice_data.get("invoicing_date"),
            invoice_data.get("acquisition_timestamp"),
            invoice_data.get("subject_by_nip"),
            invoice_data.get("subject_by_name"),
            invoice_data.get("subject_to_nip"),
            invoice_data.get("subject_to_name"),
            net_amount,
            vat_amount,
            gross_amount,
            invoice_data.get("currency", "PLN"),
            invoice_data.get("invoice_type"),
            invoice_data.get("schema_version"),
            invoice_data.get("hash_value"),
            invoice_data.get("xml_content"),
            invoice_data.get("is_issued", True),
            invoice_data.get("upo_reference"),
        ))
        await db.commit()
        return cursor.lastrowid


async def get_invoice_by_ksef_ref(ksef_reference_number: str) -> Optional[Dict]:
    """Get invoice by KSeF reference number."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM invoices WHERE ksef_reference_number = ?",
        (ksef_reference_number,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_invoices(
    is_issued: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    nip_filter: Optional[str] = None,
    invoice_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict]:
    """Get invoices with filters."""
    db = await get_db()

    query = "SELECT * FROM invoices WHERE 1=1"
    params = []

    if is_issued is not None:
        query += " AND is_issued = ?"
        params.append(is_issued)

    if date_from:
        query += " AND invoicing_date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND invoicing_date <= ?"
        params.append(date_to)

    if nip_filter:
        query += " AND (subject_by_nip LIKE ? OR subject_to_nip LIKE ?)"
        params.extend([f"%{nip_filter}%", f"%{nip_filter}%"])

    if invoice_type:
        query += " AND invoice_type = ?"
        params.append(invoice_type)

    query += " ORDER BY acquisition_timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def count_invoices(
    is_issued: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    nip_filter: Optional[str] = None,
    invoice_type: Optional[str] = None,
) -> int:
    """Count invoices with filters."""
    db = await get_db()

    query = "SELECT COUNT(*) as count FROM invoices WHERE 1=1"
    params = []

    if is_issued is not None:
        query += " AND is_issued = ?"
        params.append(is_issued)

    if date_from:
        query += " AND invoicing_date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND invoicing_date <= ?"
        params.append(date_to)

    if nip_filter:
        query += " AND (subject_by_nip LIKE ? OR subject_to_nip LIKE ?)"
        params.extend([f"%{nip_filter}%", f"%{nip_filter}%"])

    if invoice_type:
        query += " AND invoice_type = ?"
        params.append(invoice_type)

    cursor = await db.execute(query, params)
    row = await cursor.fetchone()
    return row["count"] if row else 0


async def update_invoice_xml(ksef_reference_number: str, xml_content: str) -> None:
    """Update invoice XML content."""
    db = await get_db()
    await db.execute(
        "UPDATE invoices SET xml_content = ?, updated_at = CURRENT_TIMESTAMP WHERE ksef_reference_number = ?",
        (xml_content, ksef_reference_number)
    )
    await db.commit()


async def clear_invoice_cache() -> int:
    """Clear all cached invoices. Returns count of deleted rows."""
    db = await get_db()
    cursor = await db.execute("DELETE FROM invoices")
    await db.commit()
    return cursor.rowcount


# ===== Sync Status Operations =====

async def create_sync_record(sync_type: str) -> int:
    """Create new sync status record."""
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO sync_status (sync_type, status) VALUES (?, 'running')",
        (sync_type,)
    )
    await db.commit()
    return cursor.lastrowid


async def update_sync_record(
    sync_id: int,
    status: str,
    total_fetched: int = 0,
    new_invoices: int = 0,
    updated_invoices: int = 0,
    errors: Optional[str] = None,
    last_acquisition: Optional[datetime] = None,
) -> None:
    """Update sync status record."""
    db = await get_db()
    await db.execute("""
        UPDATE sync_status SET
            status = ?,
            completed_at = CASE WHEN ? IN ('completed', 'failed') THEN CURRENT_TIMESTAMP ELSE completed_at END,
            total_fetched = ?,
            new_invoices = ?,
            updated_invoices = ?,
            errors = ?,
            last_acquisition_timestamp = ?
        WHERE id = ?
    """, (status, status, total_fetched, new_invoices, updated_invoices, errors, last_acquisition, sync_id))
    await db.commit()


async def get_last_sync(sync_type: str) -> Optional[Dict]:
    """Get last completed sync record."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM sync_status WHERE sync_type = ? AND status = 'completed' ORDER BY completed_at DESC LIMIT 1",
        (sync_type,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None
