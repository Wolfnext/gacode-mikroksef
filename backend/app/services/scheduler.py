"""Automatic synchronization scheduler using APScheduler."""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.services import database as db

logger = logging.getLogger(__name__)


class SyncScheduler:
    """Manages automatic invoice synchronization scheduling."""

    def __init__(self):
        self._scheduler: AsyncIOScheduler | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running and self._scheduler is not None

    async def start(self):
        """Start the scheduler based on saved config."""
        config = await db.get_auto_sync_config()
        settings = get_settings()

        if config is None:
            # Initialize default config from settings
            config = {
                "enabled": settings.auto_sync_enabled,
                "interval_minutes": settings.auto_sync_interval_minutes,
                "sync_issued": True,
                "sync_received": True,
            }
            await db.save_auto_sync_config(config)

        if config.get("enabled"):
            await self._start_scheduler(config)

    async def stop(self):
        """Stop the scheduler."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            self._running = False
            logger.info("Sync scheduler stopped")

    async def _start_scheduler(self, config: dict):
        """Start or restart the scheduler with given config."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)

        self._scheduler = AsyncIOScheduler()
        interval = config.get("interval_minutes", 60)

        if config.get("sync_issued", True):
            self._scheduler.add_job(
                self._sync_issued,
                trigger=IntervalTrigger(minutes=interval),
                id="sync_issued",
                name="Sync issued invoices",
                replace_existing=True,
            )

        if config.get("sync_received", True):
            self._scheduler.add_job(
                self._sync_received,
                trigger=IntervalTrigger(minutes=interval),
                id="sync_received",
                name="Sync received invoices",
                replace_existing=True,
            )

        self._scheduler.start()
        self._running = True
        logger.info(f"Sync scheduler started (interval: {interval} min)")

    async def _sync_issued(self):
        """Run automatic sync for issued invoices."""
        await self._run_sync("subject1")

    async def _sync_received(self):
        """Run automatic sync for received invoices."""
        await self._run_sync("subject2")

    async def _run_sync(self, sync_type: str):
        """Run a sync operation."""
        from app.services.session_manager import session_manager

        if not session_manager.has_active_session:
            logger.warning(f"Auto-sync skipped ({sync_type}): no active session")
            return

        try:
            from app.services.invoice_service import invoice_service
            from app.models.invoice import SubjectType

            subject_type = SubjectType.SUBJECT1 if sync_type == "subject1" else SubjectType.SUBJECT2
            result = await invoice_service.sync_invoices(subject_type=subject_type)
            logger.info(
                f"Auto-sync {sync_type}: fetched={result['total_fetched']}, "
                f"new={result['new_invoices']}"
            )
            await db.update_auto_sync_last_run(datetime.now(timezone.utc).isoformat())
        except Exception as e:
            logger.error(f"Auto-sync {sync_type} failed: {e}")

    async def update_config(self, config: dict):
        """Update auto-sync configuration and restart scheduler."""
        await db.save_auto_sync_config(config)

        if config.get("enabled"):
            await self._start_scheduler(config)
        else:
            await self.stop()

        return await db.get_auto_sync_config()

    async def get_config(self) -> dict | None:
        """Get current auto-sync configuration."""
        return await db.get_auto_sync_config()


# Singleton
sync_scheduler = SyncScheduler()
