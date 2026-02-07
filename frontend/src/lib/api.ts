/**
 * API client for mikroKSeF backend.
 */

import type {
  ApiResponse,
  InvoiceListResponse,
  InvoiceDetail,
  InvoiceQueryParams,
  SessionResponse,
  SessionStatus,
  HealthResponse,
  SyncResponse,
  SyncStatus,
} from '@/types';
import type {
  AnalyticsSummary,
  AutoSyncConfig,
  NotificationConfig,
  NotificationHistoryEntry,
} from '@/types/analytics';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

/**
 * Generic fetch wrapper with error handling.
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        // Use status text if JSON parsing fails
        errorMessage = response.statusText || errorMessage;
      }
      return { error: errorMessage };
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return { data: {} as T };
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Network error';
    return { error: message };
  }
}

// ===== Auth API =====

export const authApi = {
  /**
   * Initialize KSeF session with NIP.
   */
  initSession: (nip: string): Promise<ApiResponse<SessionResponse>> =>
    fetchApi<SessionResponse>('/auth/session/init-token', {
      method: 'POST',
      body: JSON.stringify({ nip }),
    }),

  /**
   * Get current session status.
   */
  getSessionStatus: (): Promise<ApiResponse<SessionStatus>> =>
    fetchApi<SessionStatus>('/auth/session/status'),

  /**
   * Terminate current session.
   */
  terminateSession: (): Promise<ApiResponse<{ message: string }>> =>
    fetchApi('/auth/session/terminate', { method: 'POST' }),

  /**
   * Get session info.
   */
  getSessionInfo: (): Promise<ApiResponse<Record<string, unknown>>> =>
    fetchApi('/auth/session/info'),
};

// ===== Invoices API =====

export const invoicesApi = {
  /**
   * List invoices with filters.
   */
  list: (params?: InvoiceQueryParams): Promise<ApiResponse<InvoiceListResponse>> => {
    const searchParams = new URLSearchParams();

    if (params?.subjectType) searchParams.set('subjectType', params.subjectType);
    if (params?.dateFrom) searchParams.set('dateFrom', params.dateFrom);
    if (params?.dateTo) searchParams.set('dateTo', params.dateTo);
    if (params?.amountFrom) searchParams.set('amountFrom', params.amountFrom.toString());
    if (params?.amountTo) searchParams.set('amountTo', params.amountTo.toString());
    if (params?.invoiceType) searchParams.set('invoiceType', params.invoiceType);
    if (params?.nipFilter) searchParams.set('nipFilter', params.nipFilter);
    if (params?.pageSize) searchParams.set('pageSize', params.pageSize.toString());
    if (params?.pageOffset) searchParams.set('pageOffset', params.pageOffset.toString());
    if (params?.useCache !== undefined) searchParams.set('useCache', params.useCache.toString());

    const queryString = searchParams.toString();
    return fetchApi<InvoiceListResponse>(`/invoices${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Search invoices.
   */
  search: (params: {
    q: string;
    subjectType?: 'subject1' | 'subject2';
    pageSize?: number;
    pageOffset?: number;
  }): Promise<ApiResponse<InvoiceListResponse>> => {
    const searchParams = new URLSearchParams();
    searchParams.set('q', params.q);
    if (params.subjectType) searchParams.set('subjectType', params.subjectType);
    if (params.pageSize) searchParams.set('pageSize', params.pageSize.toString());
    if (params.pageOffset) searchParams.set('pageOffset', params.pageOffset.toString());

    return fetchApi<InvoiceListResponse>(`/invoices/search?${searchParams}`);
  },

  /**
   * Get invoice detail.
   */
  get: (ksefReferenceNumber: string): Promise<ApiResponse<InvoiceDetail>> =>
    fetchApi<InvoiceDetail>(`/invoices/${encodeURIComponent(ksefReferenceNumber)}`),

  /**
   * Get invoice status.
   */
  getStatus: (ksefReferenceNumber: string): Promise<ApiResponse<Record<string, unknown>>> =>
    fetchApi(`/invoices/${encodeURIComponent(ksefReferenceNumber)}/status`),

  /**
   * Download invoice XML.
   */
  download: async (ksefReferenceNumber: string): Promise<Blob> => {
    const response = await fetch(
      `${API_BASE_URL}/invoices/${encodeURIComponent(ksefReferenceNumber)}/download`
    );

    if (!response.ok) {
      throw new Error('Download failed');
    }

    return response.blob();
  },

  /**
   * Download UPO.
   */
  downloadUpo: async (ksefReferenceNumber: string): Promise<Blob> => {
    const response = await fetch(
      `${API_BASE_URL}/invoices/${encodeURIComponent(ksefReferenceNumber)}/upo`
    );

    if (!response.ok) {
      throw new Error('UPO download failed');
    }

    return response.blob();
  },

  /**
   * Download invoice as PDF.
   */
  downloadPdf: async (ksefReferenceNumber: string): Promise<Blob> => {
    const response = await fetch(
      `${API_BASE_URL}/invoices/${encodeURIComponent(ksefReferenceNumber)}/pdf`
    );

    if (!response.ok) {
      throw new Error('PDF generation failed');
    }

    return response.blob();
  },

  /**
   * Download UPO as PDF.
   */
  downloadUpoPdf: async (ksefReferenceNumber: string): Promise<Blob> => {
    const response = await fetch(
      `${API_BASE_URL}/invoices/${encodeURIComponent(ksefReferenceNumber)}/upo-pdf`
    );

    if (!response.ok) {
      throw new Error('UPO PDF generation failed');
    }

    return response.blob();
  },
};

// ===== Sync API =====

export const syncApi = {
  /**
   * Sync invoices from KSeF.
   */
  sync: (params: {
    subjectType: 'subject1' | 'subject2';
    dateFrom?: string;
    dateTo?: string;
    fullSync?: boolean;
  }): Promise<ApiResponse<SyncResponse>> =>
    fetchApi<SyncResponse>('/sync', {
      method: 'POST',
      body: JSON.stringify({
        subjectType: params.subjectType,
        dateFrom: params.dateFrom,
        dateTo: params.dateTo,
        fullSync: params.fullSync || false,
      }),
    }),

  /**
   * Get sync status.
   */
  getStatus: (syncType: 'subject1' | 'subject2' = 'subject1'): Promise<ApiResponse<SyncStatus>> =>
    fetchApi<SyncStatus>(`/sync/status?syncType=${syncType}`),

  /**
   * Clear invoice cache.
   */
  clearCache: (): Promise<ApiResponse<{ deletedCount: number }>> =>
    fetchApi('/sync/cache', { method: 'DELETE' }),

  /**
   * Sync issued invoices.
   */
  syncIssued: (dateFrom?: string, dateTo?: string, fullSync?: boolean): Promise<ApiResponse<SyncResponse>> => {
    const params = new URLSearchParams();
    if (dateFrom) params.set('dateFrom', dateFrom);
    if (dateTo) params.set('dateTo', dateTo);
    if (fullSync) params.set('fullSync', 'true');

    return fetchApi<SyncResponse>(`/sync/issued?${params}`, { method: 'POST' });
  },

  /**
   * Sync received invoices.
   */
  syncReceived: (dateFrom?: string, dateTo?: string, fullSync?: boolean): Promise<ApiResponse<SyncResponse>> => {
    const params = new URLSearchParams();
    if (dateFrom) params.set('dateFrom', dateFrom);
    if (dateTo) params.set('dateTo', dateTo);
    if (fullSync) params.set('fullSync', 'true');

    return fetchApi<SyncResponse>(`/sync/received?${params}`, { method: 'POST' });
  },

  /**
   * Get auto-sync configuration.
   */
  getAutoSyncConfig: (): Promise<ApiResponse<AutoSyncConfig>> =>
    fetchApi<AutoSyncConfig>('/sync/auto-sync/config'),

  /**
   * Update auto-sync configuration.
   */
  updateAutoSyncConfig: (config: AutoSyncConfig): Promise<ApiResponse<AutoSyncConfig>> =>
    fetchApi<AutoSyncConfig>('/sync/auto-sync/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    }),
};

// ===== Analytics API =====

export const analyticsApi = {
  /**
   * Get analytics data.
   */
  get: (params?: {
    dateFrom?: string;
    dateTo?: string;
    months?: number;
  }): Promise<ApiResponse<AnalyticsSummary>> => {
    const searchParams = new URLSearchParams();
    if (params?.dateFrom) searchParams.set('dateFrom', params.dateFrom);
    if (params?.dateTo) searchParams.set('dateTo', params.dateTo);
    if (params?.months) searchParams.set('months', params.months.toString());

    const queryString = searchParams.toString();
    return fetchApi<AnalyticsSummary>(`/analytics${queryString ? `?${queryString}` : ''}`);
  },
};

// ===== Notifications API =====

export const notificationsApi = {
  /**
   * Get notification configuration.
   */
  getConfig: (): Promise<ApiResponse<NotificationConfig>> =>
    fetchApi<NotificationConfig>('/notifications/config'),

  /**
   * Update notification configuration.
   */
  updateConfig: (config: NotificationConfig): Promise<ApiResponse<NotificationConfig>> =>
    fetchApi<NotificationConfig>('/notifications/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    }),

  /**
   * Send test notification.
   */
  test: (): Promise<ApiResponse<{ status: string; results: Record<string, boolean> }>> =>
    fetchApi('/notifications/test', { method: 'POST' }),

  /**
   * Get notification history.
   */
  getHistory: (): Promise<ApiResponse<NotificationHistoryEntry[]>> =>
    fetchApi<NotificationHistoryEntry[]>('/notifications/history'),
};

// ===== Health API =====

export const healthApi = {
  /**
   * Check API health.
   */
  check: (): Promise<ApiResponse<HealthResponse>> =>
    fetchApi<HealthResponse>('/health'),
};

// Export all APIs
export default {
  auth: authApi,
  invoices: invoicesApi,
  sync: syncApi,
  analytics: analyticsApi,
  notifications: notificationsApi,
  health: healthApi,
};
