"""Notification configuration and history endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.models.notification import NotificationConfig, NotificationEvent
from app.services.notification_service import notification_service
from app.services import database as db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/config",
    response_model=NotificationConfig,
    summary="Get notification config",
)
async def get_notification_config():
    config = await notification_service.get_config()
    if not config:
        return NotificationConfig(enabled=False)
    return config


@router.put(
    "/config",
    response_model=NotificationConfig,
    summary="Update notification config",
)
async def update_notification_config(config: NotificationConfig):
    try:
        await notification_service.save_config(config)
        return config
    except Exception as e:
        logger.error(f"Failed to save notification config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/test",
    summary="Send test notification",
)
async def test_notification():
    config = await notification_service.get_config()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification config not found. Save config first.",
        )

    event = NotificationEvent(
        event="test",
        timestamp=datetime.utcnow(),
        newInvoices=1,
        invoiceReferences=["TEST-000-000"],
        syncType="test",
    )

    results = {}
    if config.webhook_enabled and config.webhook_url:
        results["webhook"] = await notification_service.send_webhook(event, config.webhook_url)
    if config.email_enabled and config.email_to:
        results["email"] = await notification_service.send_email(event, config)

    return {"status": "test_sent", "results": results}


@router.get(
    "/history",
    summary="Get notification history",
)
async def get_notification_history():
    rows = await db.get_notification_history(50)
    return [
        {
            "id": r.get("id"),
            "notificationType": r.get("notification_type"),
            "triggerEvent": r.get("trigger_event"),
            "recipient": r.get("recipient"),
            "status": r.get("status"),
            "errorMessage": r.get("error_message"),
            "createdAt": (r.get("created_at") or "").replace(" ", "T"),
            "sentAt": (r.get("sent_at") or "").replace(" ", "T"),
        }
        for r in rows
    ]
