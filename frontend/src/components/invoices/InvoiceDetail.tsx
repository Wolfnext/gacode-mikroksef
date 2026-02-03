'use client';

import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { formatCurrency, formatDate, formatDateTime, formatNip, getInvoiceTypeLabel, getInvoiceTypeBadgeColor } from '@/lib/utils';
import { parseInvoiceXml } from '@/lib/invoiceParser';
import type { InvoiceDetail as InvoiceDetailType, ParsedInvoice, InvoiceLineItem } from '@/types';
import { Download, FileText, ArrowLeft, ChevronDown, ChevronUp, Building2, User, FileCode } from 'lucide-react';
import Link from 'next/link';

interface InvoiceDetailViewProps {
  invoice: InvoiceDetailType;
  onDownload: () => void;
  onDownloadUpo: () => void;
}

// Party info card component
function PartyCard({ title, icon: Icon, party, nip }: {
  title: string;
  icon: React.ElementType;
  party?: ParsedInvoice['seller'];
  nip?: string;
}) {
  const displayNip = party?.nip || nip;

  return (
    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">{title}</h3>
      </div>
      <div className="space-y-1">
        <p className="font-semibold text-gray-900 dark:text-gray-100">
          {party?.name || 'Brak danych'}
        </p>
        {party?.tradeName && (
          <p className="text-sm text-gray-600 dark:text-gray-400">{party.tradeName}</p>
        )}
        {displayNip && (
          <p className="text-sm text-gray-600 dark:text-gray-400">
            NIP: <span className="font-mono">{formatNip(displayNip)}</span>
          </p>
        )}
        {party?.address && (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {party.address}
            {party.postalCode && party.city && `, ${party.postalCode} ${party.city}`}
          </p>
        )}
      </div>
    </div>
  );
}

// Line items table component
function LineItemsTable({ items }: { items: InvoiceLineItem[] }) {
  if (items.length === 0) {
    return (
      <p className="text-gray-500 dark:text-gray-400 text-center py-8">Brak pozycji do wyświetlenia</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
            <th className="px-3 py-2 text-left font-semibold w-12">Lp.</th>
            <th className="px-3 py-2 text-left font-semibold">Nazwa towaru / usługi</th>
            {items.some(i => i.pkwiu) && (
              <th className="px-3 py-2 text-left font-semibold">PKWiU</th>
            )}
            <th className="px-3 py-2 text-right font-semibold w-20">Ilość</th>
            <th className="px-3 py-2 text-left font-semibold w-16">J.m.</th>
            <th className="px-3 py-2 text-right font-semibold w-28">Cena netto</th>
            <th className="px-3 py-2 text-right font-semibold w-28">Wartość netto</th>
            <th className="px-3 py-2 text-center font-semibold w-20">VAT</th>
            <th className="px-3 py-2 text-right font-semibold w-28">Kwota VAT</th>
            <th className="px-3 py-2 text-right font-semibold w-28">Wartość brutto</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {items.map((item, idx) => {
            const vatAmount = item.vatAmount ?? (item.vatRate && item.netValue
              ? (parseFloat(item.vatRate.replace('%', '').replace(',', '.')) / 100) * item.netValue
              : 0);
            const grossValue = item.grossValue ?? (item.netValue + (vatAmount || 0));

            return (
              <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="px-3 py-2 text-gray-500 dark:text-gray-400">{item.lineNumber}</td>
                <td className="px-3 py-2">
                  <div>
                    <span className="font-medium text-gray-900 dark:text-gray-100">{item.name}</span>
                    {item.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{item.description}</p>
                    )}
                  </div>
                </td>
                {items.some(i => i.pkwiu) && (
                  <td className="px-3 py-2 text-gray-600 dark:text-gray-400 font-mono text-xs">{item.pkwiu || '-'}</td>
                )}
                <td className="px-3 py-2 text-right tabular-nums dark:text-gray-100">
                  {item.quantity?.toLocaleString('pl-PL', { maximumFractionDigits: 4 }) || '-'}
                </td>
                <td className="px-3 py-2 text-gray-600 dark:text-gray-400">{item.unit || '-'}</td>
                <td className="px-3 py-2 text-right tabular-nums dark:text-gray-100">
                  {item.unitPriceNet ? formatCurrency(item.unitPriceNet) : '-'}
                </td>
                <td className="px-3 py-2 text-right tabular-nums font-medium dark:text-gray-100">
                  {formatCurrency(item.netValue)}
                </td>
                <td className="px-3 py-2 text-center">
                  <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs font-medium dark:text-gray-200">
                    {item.vatRate || '-'}
                  </span>
                </td>
                <td className="px-3 py-2 text-right tabular-nums dark:text-gray-100">
                  {vatAmount ? formatCurrency(vatAmount) : '-'}
                </td>
                <td className="px-3 py-2 text-right tabular-nums font-medium dark:text-gray-100">
                  {formatCurrency(grossValue)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// VAT summary table
function VatSummaryTable({ summary, totalNet, totalVat, totalGross }: {
  summary?: ParsedInvoice['vatSummary'];
  totalNet?: number;
  totalVat?: number;
  totalGross?: number;
}) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
      <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
        Podsumowanie VAT
      </h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-600 dark:text-gray-400">
            <th className="text-left py-1 font-medium">Stawka</th>
            <th className="text-right py-1 font-medium">Netto</th>
            <th className="text-right py-1 font-medium">VAT</th>
            <th className="text-right py-1 font-medium">Brutto</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {summary?.map((row, idx) => (
            <tr key={idx} className="text-gray-900 dark:text-gray-100">
              <td className="py-1.5">{row.rate}</td>
              <td className="text-right py-1.5 tabular-nums">{formatCurrency(row.netValue)}</td>
              <td className="text-right py-1.5 tabular-nums">{formatCurrency(row.vatValue)}</td>
              <td className="text-right py-1.5 tabular-nums">
                {formatCurrency(row.netValue + row.vatValue)}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t-2 border-gray-300 dark:border-gray-600 font-semibold text-gray-900 dark:text-gray-100">
            <td className="py-2">RAZEM</td>
            <td className="text-right py-2 tabular-nums">
              {totalNet !== undefined ? formatCurrency(totalNet) : '-'}
            </td>
            <td className="text-right py-2 tabular-nums">
              {totalVat !== undefined ? formatCurrency(totalVat) : '-'}
            </td>
            <td className="text-right py-2 tabular-nums text-primary-600 dark:text-primary-400">
              {totalGross !== undefined ? formatCurrency(totalGross) : '-'}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

export function InvoiceDetailView({ invoice, onDownload, onDownloadUpo }: InvoiceDetailViewProps) {
  const { header, xmlContent, upoAvailable, cachedAt } = invoice;
  const [showXml, setShowXml] = useState(false);

  // Parse XML to get detailed invoice data
  const parsedInvoice = useMemo(() => {
    if (!xmlContent) return null;
    return parseInvoiceXml(xmlContent);
  }, [xmlContent]);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Back link */}
      <Link href="/invoices" className="inline-flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200">
        <ArrowLeft className="w-4 h-4 mr-1" />
        Powrót do listy
      </Link>

      {/* Invoice document */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden print:shadow-none print:border-0">
        {/* Invoice header bar */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white px-6 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold">FAKTURA</h1>
                <Badge className="bg-white/20 text-white border-white/30">
                  {getInvoiceTypeLabel(header.invoiceType)}
                </Badge>
              </div>
              <p className="text-primary-100 text-sm mt-1">
                {parsedInvoice?.invoiceNumber || header.invoiceReferenceNumber || '-'}
              </p>
            </div>

            <div className="flex items-center gap-2 print:hidden">
              <Button variant="secondary" size="sm" onClick={onDownload} className="bg-white/10 hover:bg-white/20 text-white border-white/30">
                <Download className="w-4 h-4 mr-1" />
                XML
              </Button>
              {upoAvailable && (
                <Button variant="secondary" size="sm" onClick={onDownloadUpo} className="bg-white/10 hover:bg-white/20 text-white border-white/30">
                  <FileText className="w-4 h-4 mr-1" />
                  UPO
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="p-6 space-y-6">
          {/* Dates and KSeF info */}
          <div className="flex flex-wrap gap-6 text-sm pb-4 border-b border-gray-200 dark:border-gray-700">
            <div>
              <span className="text-gray-500 dark:text-gray-400">Data wystawienia:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">{formatDate(parsedInvoice?.issueDate || header.invoicingDate)}</span>
            </div>
            {parsedInvoice?.saleDate && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Data sprzedaży:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">{formatDate(parsedInvoice.saleDate)}</span>
              </div>
            )}
            <div>
              <span className="text-gray-500 dark:text-gray-400">Data wpływu do KSeF:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">{formatDateTime(header.acquisitionTimestamp)}</span>
            </div>
            <div className="ml-auto">
              <span className="text-gray-500 dark:text-gray-400">Nr KSeF:</span>
              <span className="ml-2 font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-800 dark:text-gray-200">
                {header.ksefReferenceNumber}
              </span>
            </div>
          </div>

          {/* Parties - Seller and Buyer */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PartyCard
              title="Sprzedawca"
              icon={Building2}
              party={parsedInvoice?.seller}
              nip={header.subjectBy.identifier}
            />
            <PartyCard
              title="Nabywca"
              icon={User}
              party={parsedInvoice?.buyer}
              nip={header.subjectTo?.identifier}
            />
          </div>

          {/* Line items */}
          <div>
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3">
              Pozycje faktury
              {parsedInvoice?.itemsCount && (
                <span className="ml-2 text-gray-400 dark:text-gray-500 font-normal">
                  ({parsedInvoice.itemsCount} {parsedInvoice.itemsCount === 1 ? 'pozycja' :
                    parsedInvoice.itemsCount < 5 ? 'pozycje' : 'pozycji'})
                </span>
              )}
            </h2>
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <LineItemsTable items={parsedInvoice?.items || []} />
            </div>
          </div>

          {/* Summary section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* VAT Summary */}
            <VatSummaryTable
              summary={parsedInvoice?.vatSummary}
              totalNet={parsedInvoice?.totalNet ?? parseFloat(header.net)}
              totalVat={parsedInvoice?.totalVat ?? parseFloat(header.vat)}
              totalGross={parsedInvoice?.totalGross ?? parseFloat(header.gross)}
            />

            {/* Totals and payment */}
            <div className="space-y-4">
              {/* Grand total */}
              <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-4 border border-primary-200 dark:border-primary-800">
                <div className="text-sm text-primary-600 dark:text-primary-400 font-medium mb-1">Do zapłaty</div>
                <div className="text-3xl font-bold text-primary-700 dark:text-primary-300">
                  {formatCurrency(
                    parsedInvoice?.totalGross ?? parseFloat(header.gross),
                    parsedInvoice?.currency || header.currency
                  )}
                </div>
              </div>

              {/* Payment info */}
              {(parsedInvoice?.paymentMethod || parsedInvoice?.paymentDueDate || parsedInvoice?.bankAccount) && (
                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                  <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                    Płatność
                  </h3>
                  <div className="space-y-1 text-sm">
                    {parsedInvoice.paymentMethod && (
                      <p>
                        <span className="text-gray-500 dark:text-gray-400">Forma:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">{parsedInvoice.paymentMethod}</span>
                      </p>
                    )}
                    {parsedInvoice.paymentDueDate && (
                      <p>
                        <span className="text-gray-500 dark:text-gray-400">Termin:</span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">{formatDate(parsedInvoice.paymentDueDate)}</span>
                      </p>
                    )}
                    {parsedInvoice.bankAccount && (
                      <p>
                        <span className="text-gray-500 dark:text-gray-400">Nr konta:</span>
                        <span className="ml-2 font-mono text-xs text-gray-900 dark:text-gray-100">{parsedInvoice.bankAccount}</span>
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Notes */}
          {parsedInvoice?.notes && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border border-yellow-200 dark:border-yellow-800">
              <h3 className="text-xs font-semibold text-yellow-700 dark:text-yellow-400 uppercase tracking-wide mb-2">
                Uwagi
              </h3>
              <p className="text-sm text-yellow-800 dark:text-yellow-200">{parsedInvoice.notes}</p>
            </div>
          )}
        </div>

        {/* XML Preview (collapsible) */}
        {xmlContent && (
          <div className="border-t border-gray-200 dark:border-gray-700 print:hidden">
            <button
              onClick={() => setShowXml(!showXml)}
              className="w-full px-6 py-3 flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <span className="flex items-center gap-2">
                <FileCode className="w-4 h-4" />
                Podgląd XML
              </span>
              {showXml ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {showXml && (
              <div className="px-6 pb-6">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs font-mono max-h-96">
                  {xmlContent}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Cache info */}
      {cachedAt && (
        <p className="text-xs text-gray-400 dark:text-gray-500 text-center">
          Zapisano w cache: {formatDateTime(cachedAt)}
        </p>
      )}
    </div>
  );
}
