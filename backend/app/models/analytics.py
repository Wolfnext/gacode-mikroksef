"""Analytics and reporting models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class MonthlyTurnover(BaseModel):
    month: str
    issued_count: int = Field(alias="issuedCount")
    issued_net: float = Field(alias="issuedNet")
    issued_gross: float = Field(alias="issuedGross")
    received_count: int = Field(alias="receivedCount")
    received_net: float = Field(alias="receivedNet")
    received_gross: float = Field(alias="receivedGross")

    class Config:
        populate_by_name = True


class InvoiceTypeSummary(BaseModel):
    invoice_type: str = Field(alias="invoiceType")
    count: int
    net_total: float = Field(alias="netTotal")
    vat_total: float = Field(alias="vatTotal")
    gross_total: float = Field(alias="grossTotal")

    class Config:
        populate_by_name = True


class TopCounterparty(BaseModel):
    nip: str
    name: str
    invoice_count: int = Field(alias="invoiceCount")
    total_gross: float = Field(alias="totalGross")

    class Config:
        populate_by_name = True


class AnalyticsSummary(BaseModel):
    invoice_count: int = Field(alias="invoiceCount")
    total_issued: float = Field(alias="totalIssued")
    total_received: float = Field(alias="totalReceived")
    monthly_turnover: List[MonthlyTurnover] = Field(alias="monthlyTurnover")
    type_summary: List[InvoiceTypeSummary] = Field(alias="typeSummary")
    top_issued_counterparties: List[TopCounterparty] = Field(alias="topIssuedCounterparties")
    top_received_counterparties: List[TopCounterparty] = Field(alias="topReceivedCounterparties")

    class Config:
        populate_by_name = True
