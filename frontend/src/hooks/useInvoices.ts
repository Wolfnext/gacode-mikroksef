'use client';

/**
 * Invoices hook for fetching and managing invoice data.
 */

import { useState, useCallback, useRef } from 'react';
import { invoicesApi } from '@/lib/api';
import { downloadBlob } from '@/lib/utils';
import type { InvoiceHeader, InvoiceQueryParams, InvoiceDetail } from '@/types';

interface UseInvoicesReturn {
  invoices: InvoiceHeader[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  pageSize: number;
  pageOffset: number;
  hasMore: boolean;
  fetchInvoices: (params?: InvoiceQueryParams) => Promise<void>;
  fetchInvoiceDetail: (ksefRef: string) => Promise<InvoiceDetail | null>;
  downloadInvoice: (ksefRef: string) => Promise<void>;
  downloadUpo: (ksefRef: string) => Promise<void>;
  setPageOffset: (offset: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  clearError: () => void;
}

export function useInvoices(initialPageSize = 50): UseInvoicesReturn {
  const [invoices, setInvoices] = useState<InvoiceHeader[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(initialPageSize);
  const [pageOffset, setPageOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const lastParamsRef = useRef<InvoiceQueryParams>({});

  // Fetch invoices with params
  const fetchInvoices = useCallback(
    async (params?: InvoiceQueryParams) => {
      setLoading(true);
      setError(null);

      const queryParams: InvoiceQueryParams = {
        pageSize,
        pageOffset,
        ...lastParamsRef.current,
        ...params,
      };

      // Update last params if new params provided
      if (params) {
        lastParamsRef.current = params;
      }

      const { data, error: apiError } = await invoicesApi.list(queryParams);

      if (data) {
        setInvoices(data.invoiceHeaderList);
        setTotalCount(data.numberOfElements);
        setHasMore(data.hasMore);
      } else {
        setError(apiError || 'Nie udało się pobrać faktur');
        setInvoices([]);
      }

      setLoading(false);
    },
    [pageSize, pageOffset]
  );

  // Fetch invoice detail
  const fetchInvoiceDetail = useCallback(
    async (ksefRef: string): Promise<InvoiceDetail | null> => {
      setLoading(true);
      setError(null);

      const { data, error: apiError } = await invoicesApi.get(ksefRef);

      setLoading(false);

      if (data) {
        return data;
      } else {
        setError(apiError || 'Nie udało się pobrać szczegółów faktury');
        return null;
      }
    },
    []
  );

  // Download invoice XML
  const downloadInvoice = useCallback(async (ksefRef: string) => {
    try {
      const blob = await invoicesApi.download(ksefRef);
      downloadBlob(blob, `${ksefRef}.xml`);
    } catch (e) {
      setError('Nie udało się pobrać pliku faktury');
    }
  }, []);

  // Download UPO
  const downloadUpo = useCallback(async (ksefRef: string) => {
    try {
      const blob = await invoicesApi.downloadUpo(ksefRef);
      downloadBlob(blob, `UPO_${ksefRef}.xml`);
    } catch (e) {
      setError('Nie udało się pobrać UPO');
    }
  }, []);

  // Pagination
  const nextPage = useCallback(() => {
    if (pageOffset + pageSize < totalCount) {
      const newOffset = pageOffset + pageSize;
      setPageOffset(newOffset);
      fetchInvoices({ ...lastParamsRef.current, pageOffset: newOffset });
    }
  }, [pageOffset, pageSize, totalCount, fetchInvoices]);

  const prevPage = useCallback(() => {
    if (pageOffset > 0) {
      const newOffset = Math.max(0, pageOffset - pageSize);
      setPageOffset(newOffset);
      fetchInvoices({ ...lastParamsRef.current, pageOffset: newOffset });
    }
  }, [pageOffset, pageSize, fetchInvoices]);

  const clearError = useCallback(() => setError(null), []);

  return {
    invoices,
    loading,
    error,
    totalCount,
    pageSize,
    pageOffset,
    hasMore,
    fetchInvoices,
    fetchInvoiceDetail,
    downloadInvoice,
    downloadUpo,
    setPageOffset,
    nextPage,
    prevPage,
    clearError,
  };
}
