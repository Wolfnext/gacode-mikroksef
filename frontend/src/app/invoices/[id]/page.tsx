'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Alert } from '@/components/ui/Alert';
import { Spinner } from '@/components/ui/Spinner';
import { InvoiceDetailView } from '@/components/invoices/InvoiceDetail';
import { useAuth } from '@/hooks/useAuth';
import { useInvoices } from '@/hooks/useInvoices';
import type { InvoiceDetail } from '@/types';

export default function InvoiceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const ksefRef = decodeURIComponent(params.id as string);

  const { isAuthenticated, sessionStatus, loading: authLoading, logout, refresh } = useAuth();
  const {
    loading,
    error,
    fetchInvoiceDetail,
    downloadInvoice,
    downloadUpo,
    downloadPdf,
    downloadUpoPdf,
    clearError,
  } = useInvoices();

  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Fetch invoice detail
  useEffect(() => {
    if (isAuthenticated && ksefRef) {
      fetchInvoiceDetail(ksefRef).then((detail) => {
        if (detail) {
          setInvoice(detail);
        }
      });
    }
  }, [isAuthenticated, ksefRef, fetchInvoiceDetail]);

  if (authLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <Spinner size="lg" />
      </main>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header
        session={sessionStatus}
        onRefresh={refresh}
        onLogout={logout}
        loading={authLoading}
      />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <Alert variant="error" className="mb-6" onClose={clearError}>
            {error}
          </Alert>
        )}

        {loading && !invoice ? (
          <div className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : invoice ? (
          <InvoiceDetailView
            invoice={invoice}
            onDownload={() => downloadInvoice(ksefRef)}
            onDownloadUpo={() => downloadUpo(ksefRef)}
            onDownloadPdf={() => downloadPdf(ksefRef)}
            onDownloadUpoPdf={() => downloadUpoPdf(ksefRef)}
          />
        ) : (
          <Alert variant="error">
            Nie znaleziono faktury o podanym numerze KSeF
          </Alert>
        )}
      </main>
    </div>
  );
}
