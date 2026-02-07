/**
 * Analytics, auto-sync, and notification type definitions.
 */

export interface MonthlyTurnover {
  month: string;
  issuedCount: number;
  issuedNet: number;
  issuedGross: number;
  receivedCount: number;
  receivedNet: number;
  receivedGross: number;
}

export interface InvoiceTypeSummary {
  invoiceType: string;
  count: number;
  netTotal: number;
  vatTotal: number;
  grossTotal: number;
}

export interface TopCounterparty {
  nip: string;
  name: string;
  invoiceCount: number;
  totalGross: number;
}

export interface AnalyticsSummary {
  invoiceCount: number;
  totalIssued: number;
  totalReceived: number;
  monthlyTurnover: MonthlyTurnover[];
  typeSummary: InvoiceTypeSummary[];
  topIssuedCounterparties: TopCounterparty[];
  topReceivedCounterparties: TopCounterparty[];
}

export interface AutoSyncConfig {
  enabled: boolean;
  intervalMinutes: number;
  syncIssued: boolean;
  syncReceived: boolean;
  lastRunAt?: string;
}

export interface NotificationConfig {
  enabled: boolean;
  webhookUrl?: string;
  webhookEnabled: boolean;
  emailEnabled: boolean;
  emailTo?: string;
  smtpHost?: string;
  smtpPort: number;
  smtpUsername?: string;
  smtpPassword?: string;
  smtpUseTls: boolean;
}

export interface NotificationHistoryEntry {
  id: number;
  notificationType: string;
  triggerEvent: string;
  recipient?: string;
  status: string;
  errorMessage?: string;
  createdAt: string;
  sentAt?: string;
}
