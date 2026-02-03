'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { formatCurrency, formatDate, truncateKsefRef, getInvoiceTypeLabel, getInvoiceTypeBadgeColor } from '@/lib/utils';
import type { InvoiceHeader } from '@/types';
import { Download, Eye, ChevronLeft, ChevronRight } from 'lucide-react';

interface InvoiceListProps {
  invoices: InvoiceHeader[];
  loading: boolean;
  totalCount: number;
  pageSize: number;
  pageOffset: number;
  subjectType: 'subject1' | 'subject2';
  onDownload: (ksefRef: string) => void;
  onNextPage: () => void;
  onPrevPage: () => void;
}

export function InvoiceList({
  invoices,
  loading,
  totalCount,
  pageSize,
  pageOffset,
  subjectType,
  onDownload,
  onNextPage,
  onPrevPage,
}: InvoiceListProps) {
  const currentPage = Math.floor(pageOffset / pageSize) + 1;
  const totalPages = Math.ceil(totalCount / pageSize);

  if (loading && invoices.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (invoices.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">Brak faktur do wyświetlenia</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
          Użyj przycisku "Synchronizuj" aby pobrać faktury z KSeF
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Numer KSeF
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Data
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                {subjectType === 'subject1' ? 'Nabywca' : 'Sprzedawca'}
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Typ
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Netto
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                VAT
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Brutto
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Akcje
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {invoices.map((invoice) => {
              const counterparty = subjectType === 'subject1'
                ? invoice.subjectTo
                : invoice.subjectBy;

              return (
                <tr
                  key={invoice.ksefReferenceNumber}
                  className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <td className="px-4 py-4 whitespace-nowrap">
                    <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded font-mono text-gray-800 dark:text-gray-200">
                      {truncateKsefRef(invoice.ksefReferenceNumber)}
                    </code>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                    {formatDate(invoice.invoicingDate)}
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm">
                      <p className="font-medium text-gray-900 dark:text-gray-100 truncate max-w-[200px]">
                        {counterparty?.name || 'Brak nazwy'}
                      </p>
                      <p className="text-gray-500 dark:text-gray-400 text-xs">
                        NIP: {counterparty?.identifier || '-'}
                      </p>
                    </div>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <Badge className={getInvoiceTypeBadgeColor(invoice.invoiceType)}>
                      {getInvoiceTypeLabel(invoice.invoiceType)}
                    </Badge>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
                    {formatCurrency(invoice.net)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-right text-gray-500 dark:text-gray-400">
                    {formatCurrency(invoice.vat)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900 dark:text-gray-100">
                    {formatCurrency(invoice.gross)}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Link href={`/invoices/${encodeURIComponent(invoice.ksefReferenceNumber)}`}>
                        <Button variant="ghost" size="sm" title="Szczegóły">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDownload(invoice.ksefReferenceNumber)}
                        title="Pobierz XML"
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Wyświetlono {pageOffset + 1} - {Math.min(pageOffset + pageSize, totalCount)} z {totalCount} faktur
        </p>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={onPrevPage}
            disabled={pageOffset === 0 || loading}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Poprzednia
          </Button>

          <span className="text-sm text-gray-600 dark:text-gray-400 px-2">
            Strona {currentPage} z {totalPages}
          </span>

          <Button
            variant="secondary"
            size="sm"
            onClick={onNextPage}
            disabled={pageOffset + pageSize >= totalCount || loading}
          >
            Następna
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
}
