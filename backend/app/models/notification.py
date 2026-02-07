"""Notification models."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class NotificationConfig(BaseModel):
    enabled: bool = False
    webhook_url: Optional[str] = Field(None, alias="webhookUrl")
    webhook_enabled: bool = Field(False, alias="webhookEnabled")
    email_enabled: bool = Field(False, alias="emailEnabled")
    email_to: Optional[str] = Field(None, alias="emailTo")
    smtp_host: Optional[str] = Field(None, alias="smtpHost")
    smtp_port: int = Field(587, alias="smtpPort")
    smtp_username: Optional[str] = Field(None, alias="smtpUsername")
    smtp_password: Optional[str] = Field(None, alias="smtpPassword")
    smtp_use_tls: bool = Field(True, alias="smtpUseTls")

    class Config:
        populate_by_name = True


class NotificationEvent(BaseModel):
    event: str
    timestamp: datetime
    new_invoices: int = Field(alias="newInvoices")
    invoice_references: List[str] = Field(default_factory=list, alias="invoiceReferences")
    sync_type: str = Field(alias="syncType")

    class Config:
        populate_by_name = True
