/**
 * TypeScript type definitions for mikroKSeF frontend.
 */

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

// Subject (company/person) info
export interface SubjectInfo {
  identifierType: string;
  identifier: string;
  name?: string;
  tradeName?: string;
}

// Hash type
export interface HashSHA {
  algorithm: string;
  encoding: string;
  value: string;
}

// Invoice header
export interface InvoiceHeader {
  invoiceReferenceNumber: string;
  ksefReferenceNumber: string;
  invoiceHash?: HashSHA;
  invoicingDate: string;
  acquisitionTimestamp: string;
  subjectBy: SubjectInfo;
  subjectTo?: SubjectInfo;
  net: string;
  vat: string;
  gross: string;
  currency: string;
  schemaVersion?: string;
  invoiceType: 'VAT' | 'KOR' | 'ZAL' | 'ROZ';
}

// Invoice list response
export interface InvoiceListResponse {
  timestamp: string;
  referenceNumber: string;
  numberOfElements: number;
  pageSize: number;
  pageOffset: number;
  hasMore: boolean;
  invoiceHeaderList: InvoiceHeader[];
}

// Invoice detail
export interface InvoiceDetail {
  header: InvoiceHeader;
  xmlContent?: string;
  upoAvailable: boolean;
  cachedAt?: string;
}

// Query parameters
export interface InvoiceQueryParams {
  subjectType?: 'subject1' | 'subject2';
  dateFrom?: string;
  dateTo?: string;
  amountFrom?: number;
  amountTo?: number;
  invoiceType?: string;
  nipFilter?: string;
  pageSize?: number;
  pageOffset?: number;
  useCache?: boolean;
}

// Session response
export interface SessionResponse {
  sessionToken: string;
  referenceNumber: string;
  timestamp: string;
}

// Session status
export interface SessionStatus {
  referenceNumber: string;
  processingCode: number;
  processingDescription: string;
  numberOfElements: number;
  timestamp: string;
  isActive: boolean;
}

// Health response
export interface HealthResponse {
  status: string;
  environment: string;
  ksefApi: string;
  sessionActive: boolean;
  sessionReference?: string;
  databaseConnected: boolean;
  timestamp: string;
  version: string;
}

// Sync response
export interface SyncResponse {
  status: string;
  totalFetched: number;
  newInvoices: number;
  updatedInvoices: number;
  errors: string[];
  startedAt: string;
  completedAt?: string;
}

// Sync status
export interface SyncStatus {
  status: string;
  syncType: string;
  startedAt?: string;
  completedAt?: string;
  totalFetched: number;
  newInvoices: number;
  updatedInvoices: number;
  lastAcquisitionTimestamp?: string;
  message?: string;
}

// Invoice type labels
export const INVOICE_TYPE_LABELS: Record<string, string> = {
  VAT: 'Faktura VAT',
  KOR: 'Korekta',
  ZAL: 'Faktura zaliczkowa',
  ROZ: 'Faktura rozliczeniowa',
};

// Subject type labels
export const SUBJECT_TYPE_LABELS: Record<string, string> = {
  subject1: 'Wystawione',
  subject2: 'Otrzymane',
};

// Parsed invoice line item (from XML)
export interface InvoiceLineItem {
  lineNumber: number;
  name: string;
  description?: string;
  quantity?: number;
  unit?: string;
  unitPriceNet?: number;
  netValue: number;
  vatRate?: string;
  vatAmount?: number;
  grossValue?: number;
  pkwiu?: string;
  gtin?: string;
  cn?: string;
}

// Parsed invoice data (from XML)
export interface ParsedInvoice {
  // Header info
  invoiceNumber?: string;
  issueDate?: string;
  saleDate?: string;
  currency?: string;

  // Seller
  seller?: {
    name?: string;
    tradeName?: string;
    nip?: string;
    address?: string;
    city?: string;
    postalCode?: string;
    country?: string;
  };

  // Buyer
  buyer?: {
    name?: string;
    tradeName?: string;
    nip?: string;
    address?: string;
    city?: string;
    postalCode?: string;
    country?: string;
  };

  // Line items
  items: InvoiceLineItem[];
  itemsCount?: number;
  itemsTotalNet?: number;

  // VAT summary by rate
  vatSummary?: Array<{
    rate: string;
    netValue: number;
    vatValue: number;
  }>;

  // Totals
  totalNet?: number;
  totalVat?: number;
  totalGross?: number;

  // Payment
  paymentMethod?: string;
  paymentDueDate?: string;
  bankAccount?: string;

  // Additional
  notes?: string;
}
