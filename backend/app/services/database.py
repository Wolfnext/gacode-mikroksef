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

        -- Auto-sync configuration
        CREATE TABLE IF NOT EXISTS auto_sync_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enabled BOOLEAN DEFAULT 0,
            interval_minutes INTEGER DEFAULT 60,
            sync_issued BOOLEAN DEFAULT 1,
            sync_received BOOLEAN DEFAULT 1,
            last_run_at DATETIME,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Notification configuration
        CREATE TABLE IF NOT EXISTS notification_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enabled BOOLEAN DEFAULT 0,
            webhook_url TEXT,
            webhook_enabled BOOLEAN DEFAULT 0,
            email_enabled BOOLEAN DEFAULT 0,
            email_to TEXT,
            smtp_host TEXT,
            smtp_port INTEGER DEFAULT 587,
            smtp_username TEXT,
            smtp_password TEXT,
            smtp_use_tls BOOLEAN DEFAULT 1,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Notification history
        CREATE TABLE IF NOT EXISTS notification_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notification_type TEXT NOT NULL,
            trigger_event TEXT NOT NULL,
            recipient TEXT,
            payload TEXT,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            sent_at DATETIME
        );

        CREATE INDEX IF NOT EXISTS idx_notification_history_created
            ON notification_history(created_at);
    """)

    await _db.commit()

    # FTS5 virtual table (must be created separately)
    try:
        await _db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS invoices_fts USING fts5(
                ksef_reference_number UNINDEXED,
                invoice_reference_number,
                subject_by_name,
                subject_to_name,
                search_content
            )
        """)
        await _db.commit()
    except Exception as e:
        logger.warning(f"FTS5 table creation: {e}")

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

        # Add to FTS index
        try:
            await db.execute(
                "INSERT INTO invoices_fts(ksef_reference_number, invoice_reference_number, subject_by_name, subject_to_name, search_content) VALUES (?, ?, ?, ?, ?)",
                (
                    invoice_data.get("ksef_reference_number"),
                    invoice_data.get("invoice_reference_number", ""),
                    invoice_data.get("subject_by_name", ""),
                    invoice_data.get("subject_to_name", ""),
                    "",
                ),
            )
            await db.commit()
        except Exception:
            pass  # FTS insert failure is non-critical

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


# ===== Full-Text Search Operations =====

async def upsert_fts(
    ksef_reference_number: str,
    invoice_reference_number: str = "",
    subject_by_name: str = "",
    subject_to_name: str = "",
    search_content: str = "",
) -> None:
    """Insert or replace an FTS entry for an invoice."""
    db = await get_db()
    # Delete old entry if exists
    await db.execute(
        "DELETE FROM invoices_fts WHERE ksef_reference_number = ?",
        (ksef_reference_number,)
    )
    await db.execute(
        "INSERT INTO invoices_fts(ksef_reference_number, invoice_reference_number, subject_by_name, subject_to_name, search_content) VALUES (?, ?, ?, ?, ?)",
        (ksef_reference_number, invoice_reference_number or "", subject_by_name or "", subject_to_name or "", search_content or ""),
    )
    await db.commit()


async def update_invoice_search_content(ksef_reference_number: str, search_content: str) -> None:
    """Update searchable content for an invoice in FTS."""
    db = await get_db()
    # Check if FTS entry exists
    cursor = await db.execute(
        "SELECT ksef_reference_number FROM invoices_fts WHERE ksef_reference_number = ?",
        (ksef_reference_number,)
    )
    row = await cursor.fetchone()
    if row:
        # Delete and re-insert (FTS5 doesn't support UPDATE well for content)
        inv = await get_invoice_by_ksef_ref(ksef_reference_number)
        if inv:
            await db.execute("DELETE FROM invoices_fts WHERE ksef_reference_number = ?", (ksef_reference_number,))
            await db.execute(
                "INSERT INTO invoices_fts(ksef_reference_number, invoice_reference_number, subject_by_name, subject_to_name, search_content) VALUES (?, ?, ?, ?, ?)",
                (ksef_reference_number, inv.get("invoice_reference_number", ""), inv.get("subject_by_name", ""), inv.get("subject_to_name", ""), search_content),
            )
            await db.commit()


async def search_invoices(
    search_query: str,
    is_issued: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict]:
    """Full-text search across invoices using FTS5."""
    db = await get_db()

    query = """
        SELECT i.*
        FROM invoices i
        JOIN invoices_fts fts ON i.ksef_reference_number = fts.ksef_reference_number
        WHERE invoices_fts MATCH ?
    """
    params: list = [search_query]

    if is_issued is not None:
        query += " AND i.is_issued = ?"
        params.append(is_issued)

    query += " ORDER BY bm25(invoices_fts) LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def count_search_results(
    search_query: str,
    is_issued: Optional[bool] = None,
) -> int:
    """Count full-text search results."""
    db = await get_db()

    query = """
        SELECT COUNT(*) as count
        FROM invoices i
        JOIN invoices_fts fts ON i.ksef_reference_number = fts.ksef_reference_number
        WHERE invoices_fts MATCH ?
    """
    params: list = [search_query]

    if is_issued is not None:
        query += " AND i.is_issued = ?"
        params.append(is_issued)

    cursor = await db.execute(query, params)
    row = await cursor.fetchone()
    return row["count"] if row else 0


async def rebuild_fts_index() -> int:
    """Rebuild FTS index from existing invoices."""
    db = await get_db()
    await db.execute("DELETE FROM invoices_fts")
    cursor = await db.execute(
        "SELECT ksef_reference_number, invoice_reference_number, subject_by_name, subject_to_name FROM invoices"
    )
    rows = await cursor.fetchall()
    count = 0
    for row in rows:
        await db.execute(
            "INSERT INTO invoices_fts(ksef_reference_number, invoice_reference_number, subject_by_name, subject_to_name, search_content) VALUES (?, ?, ?, ?, ?)",
            (row["ksef_reference_number"], row["invoice_reference_number"] or "", row["subject_by_name"] or "", row["subject_to_name"] or "", ""),
        )
        count += 1
    await db.commit()
    return count


# ===== Analytics Operations =====

async def get_monthly_turnover(
    months: int = 12,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict]:
    """Get monthly turnover summary."""
    db = await get_db()

    query = """
        SELECT
            strftime('%Y-%m', invoicing_date) as month,
            SUM(CASE WHEN is_issued = 1 THEN 1 ELSE 0 END) as issued_count,
            SUM(CASE WHEN is_issued = 1 THEN net_amount ELSE 0 END) as issued_net,
            SUM(CASE WHEN is_issued = 1 THEN gross_amount ELSE 0 END) as issued_gross,
            SUM(CASE WHEN is_issued = 0 THEN 1 ELSE 0 END) as received_count,
            SUM(CASE WHEN is_issued = 0 THEN net_amount ELSE 0 END) as received_net,
            SUM(CASE WHEN is_issued = 0 THEN gross_amount ELSE 0 END) as received_gross
        FROM invoices
        WHERE invoicing_date IS NOT NULL
    """
    params: list = []

    if date_from:
        query += " AND invoicing_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND invoicing_date <= ?"
        params.append(date_to)

    query += " GROUP BY month ORDER BY month DESC LIMIT ?"
    params.append(months)

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_invoice_type_summary(
    is_issued: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict]:
    """Get invoice count and totals by type."""
    db = await get_db()

    query = """
        SELECT
            invoice_type,
            COUNT(*) as count,
            SUM(net_amount) as net_total,
            SUM(vat_amount) as vat_total,
            SUM(gross_amount) as gross_total
        FROM invoices
        WHERE 1=1
    """
    params: list = []

    if is_issued is not None:
        query += " AND is_issued = ?"
        params.append(is_issued)
    if date_from:
        query += " AND invoicing_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND invoicing_date <= ?"
        params.append(date_to)

    query += " GROUP BY invoice_type ORDER BY count DESC"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_top_counterparties(
    is_issued: bool = True,
    limit: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict]:
    """Get top counterparties by gross amount."""
    db = await get_db()

    if is_issued:
        nip_col = "subject_to_nip"
        name_col = "subject_to_name"
    else:
        nip_col = "subject_by_nip"
        name_col = "subject_by_name"

    query = f"""
        SELECT
            {nip_col} as nip,
            {name_col} as name,
            COUNT(*) as invoice_count,
            SUM(gross_amount) as total_gross
        FROM invoices
        WHERE is_issued = ? AND {nip_col} IS NOT NULL AND {nip_col} != ''
    """
    params: list = [is_issued]

    if date_from:
        query += " AND invoicing_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND invoicing_date <= ?"
        params.append(date_to)

    query += f" GROUP BY {nip_col} ORDER BY total_gross DESC LIMIT ?"
    params.append(limit)

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_totals(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict:
    """Get total issued and received amounts."""
    db = await get_db()

    query = """
        SELECT
            COUNT(*) as invoice_count,
            SUM(CASE WHEN is_issued = 1 THEN gross_amount ELSE 0 END) as total_issued,
            SUM(CASE WHEN is_issued = 0 THEN gross_amount ELSE 0 END) as total_received
        FROM invoices
        WHERE 1=1
    """
    params: list = []

    if date_from:
        query += " AND invoicing_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND invoicing_date <= ?"
        params.append(date_to)

    cursor = await db.execute(query, params)
    row = await cursor.fetchone()
    return dict(row) if row else {"invoice_count": 0, "total_issued": 0, "total_received": 0}


# ===== Auto-Sync Config Operations =====

async def get_auto_sync_config() -> Optional[Dict]:
    """Get auto-sync configuration."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM auto_sync_config ORDER BY id DESC LIMIT 1")
    row = await cursor.fetchone()
    return dict(row) if row else None


async def save_auto_sync_config(
    enabled: bool,
    interval_minutes: int,
    sync_issued: bool,
    sync_received: bool,
) -> None:
    """Save auto-sync configuration."""
    db = await get_db()
    cursor = await db.execute("SELECT id FROM auto_sync_config LIMIT 1")
    existing = await cursor.fetchone()

    if existing:
        await db.execute("""
            UPDATE auto_sync_config SET
                enabled = ?, interval_minutes = ?, sync_issued = ?,
                sync_received = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (enabled, interval_minutes, sync_issued, sync_received, existing["id"]))
    else:
        await db.execute("""
            INSERT INTO auto_sync_config (enabled, interval_minutes, sync_issued, sync_received)
            VALUES (?, ?, ?, ?)
        """, (enabled, interval_minutes, sync_issued, sync_received))
    await db.commit()


async def update_auto_sync_last_run() -> None:
    """Update auto-sync last run timestamp."""
    db = await get_db()
    await db.execute(
        "UPDATE auto_sync_config SET last_run_at = CURRENT_TIMESTAMP WHERE id = (SELECT id FROM auto_sync_config ORDER BY id DESC LIMIT 1)"
    )
    await db.commit()


# ===== Notification Operations =====

async def get_notification_config() -> Optional[Dict]:
    """Get notification configuration."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM notification_config ORDER BY id DESC LIMIT 1")
    row = await cursor.fetchone()
    return dict(row) if row else None


async def save_notification_config(config: Dict) -> None:
    """Save notification configuration."""
    db = await get_db()
    cursor = await db.execute("SELECT id FROM notification_config LIMIT 1")
    existing = await cursor.fetchone()

    if existing:
        await db.execute("""
            UPDATE notification_config SET
                enabled = ?, webhook_url = ?, webhook_enabled = ?,
                email_enabled = ?, email_to = ?,
                smtp_host = ?, smtp_port = ?, smtp_username = ?,
                smtp_password = ?, smtp_use_tls = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            config.get("enabled", False), config.get("webhook_url"),
            config.get("webhook_enabled", False), config.get("email_enabled", False),
            config.get("email_to"), config.get("smtp_host"),
            config.get("smtp_port", 587), config.get("smtp_username"),
            config.get("smtp_password"), config.get("smtp_use_tls", True),
            existing["id"],
        ))
    else:
        await db.execute("""
            INSERT INTO notification_config (
                enabled, webhook_url, webhook_enabled, email_enabled, email_to,
                smtp_host, smtp_port, smtp_username, smtp_password, smtp_use_tls
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config.get("enabled", False), config.get("webhook_url"),
            config.get("webhook_enabled", False), config.get("email_enabled", False),
            config.get("email_to"), config.get("smtp_host"),
            config.get("smtp_port", 587), config.get("smtp_username"),
            config.get("smtp_password"), config.get("smtp_use_tls", True),
        ))
    await db.commit()


async def add_notification_history(
    notification_type: str,
    trigger_event: str,
    recipient: Optional[str],
    payload: str,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    """Add notification history entry."""
    db = await get_db()
    await db.execute("""
        INSERT INTO notification_history (
            notification_type, trigger_event, recipient, payload, status,
            error_message, sent_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        notification_type, trigger_event, recipient, payload, status,
        error_message, datetime.utcnow() if status == "sent" else None,
    ))
    await db.commit()


async def get_notification_history(limit: int = 50) -> List[Dict]:
    """Get recent notification history."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM notification_history ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
