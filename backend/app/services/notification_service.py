"""Notification service for webhooks and emails."""

import json
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import httpx

from app.services import database as db
from app.models.notification import NotificationConfig, NotificationEvent

logger = logging.getLogger(__name__)


class NotificationService:

    async def get_config(self) -> Optional[NotificationConfig]:
        row = await db.get_notification_config()
        if row:
            return NotificationConfig(
                enabled=bool(row.get("enabled")),
                webhookUrl=row.get("webhook_url"),
                webhookEnabled=bool(row.get("webhook_enabled")),
                emailEnabled=bool(row.get("email_enabled")),
                emailTo=row.get("email_to"),
                smtpHost=row.get("smtp_host"),
                smtpPort=row.get("smtp_port", 587),
                smtpUsername=row.get("smtp_username"),
                smtpPassword=row.get("smtp_password"),
                smtpUseTls=bool(row.get("smtp_use_tls", True)),
            )
        return None

    async def save_config(self, config: NotificationConfig) -> None:
        await db.save_notification_config(config.model_dump(by_alias=False))

    async def send_webhook(self, event: NotificationEvent, webhook_url: str) -> bool:
        payload = event.model_dump(by_alias=True, mode="json")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                success = response.status_code in (200, 201, 204)

                await db.add_notification_history(
                    notification_type="webhook",
                    trigger_event=event.event,
                    recipient=webhook_url,
                    payload=json.dumps(payload),
                    status="sent" if success else "failed",
                    error_message=None if success else f"HTTP {response.status_code}",
                )
                return success
        except Exception as e:
            logger.error(f"Webhook failed: {e}")
            await db.add_notification_history(
                notification_type="webhook",
                trigger_event=event.event,
                recipient=webhook_url,
                payload=json.dumps(payload),
                status="failed",
                error_message=str(e),
            )
            return False

    async def send_email(self, event: NotificationEvent, config: NotificationConfig) -> bool:
        if not config.email_to or not config.smtp_host:
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"mikroKSeF: {event.new_invoices} nowych faktur"
            msg["From"] = config.smtp_username or config.email_to
            msg["To"] = config.email_to

            refs = "\n".join(f"- {ref}" for ref in event.invoice_references[:10])
            text = f"Wykryto {event.new_invoices} nowych faktur.\nTyp: {event.sync_type}\n\n{refs}"

            html_refs = "".join(f"<li>{ref}</li>" for ref in event.invoice_references[:10])
            html = f"<h2>mikroKSeF</h2><p>Wykryto <b>{event.new_invoices}</b> nowych faktur ({event.sync_type}).</p><ul>{html_refs}</ul>"

            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
                if config.smtp_use_tls:
                    server.starttls()
                if config.smtp_username and config.smtp_password:
                    server.login(config.smtp_username, config.smtp_password)
                server.send_message(msg)

            await db.add_notification_history(
                notification_type="email",
                trigger_event=event.event,
                recipient=config.email_to,
                payload=json.dumps(event.model_dump(by_alias=True, mode="json")),
                status="sent",
            )
            return True
        except Exception as e:
            logger.error(f"Email failed: {e}")
            await db.add_notification_history(
                notification_type="email",
                trigger_event=event.event,
                recipient=config.email_to,
                payload=json.dumps(event.model_dump(by_alias=True, mode="json")),
                status="failed",
                error_message=str(e),
            )
            return False

    async def notify_new_invoices(
        self,
        new_invoice_count: int,
        invoice_references: List[str],
        sync_type: str,
    ) -> None:
        if new_invoice_count == 0:
            return

        config = await self.get_config()
        if not config or not config.enabled:
            return

        event = NotificationEvent(
            event="new_invoice",
            timestamp=datetime.utcnow(),
            newInvoices=new_invoice_count,
            invoiceReferences=invoice_references,
            syncType=sync_type,
        )

        if config.webhook_enabled and config.webhook_url:
            await self.send_webhook(event, config.webhook_url)

        if config.email_enabled and config.email_to:
            await self.send_email(event, config)


notification_service = NotificationService()
