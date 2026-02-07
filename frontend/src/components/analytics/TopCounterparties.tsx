'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import type { TopCounterparty } from '@/types/analytics';

interface TopCounterpartiesProps {
  title: string;
  data: TopCounterparty[];
}

function fmt(value: number): string {
  return value.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatNip(nip: string): string {
  if (nip.length === 10) {
    return `${nip.slice(0, 3)}-${nip.slice(3, 6)}-${nip.slice(6, 8)}-${nip.slice(8)}`;
  }
  return nip;
}

export function TopCounterparties({ title, data }: TopCounterpartiesProps) {
  if (data.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b dark:border-gray-700">
                <th className="text-left py-2 font-medium text-gray-600 dark:text-gray-400">Kontrahent</th>
                <th className="text-left py-2 font-medium text-gray-600 dark:text-gray-400">NIP</th>
                <th className="text-right py-2 font-medium text-gray-600 dark:text-gray-400">Faktury</th>
                <th className="text-right py-2 font-medium text-gray-600 dark:text-gray-400">Brutto</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => (
                <tr key={`${row.nip}-${idx}`} className="border-b dark:border-gray-700">
                  <td className="py-2 text-gray-900 dark:text-gray-100 truncate max-w-[200px]">
                    {row.name || '-'}
                  </td>
                  <td className="py-2 text-gray-600 dark:text-gray-400 font-mono text-xs">
                    {formatNip(row.nip)}
                  </td>
                  <td className="text-right py-2 text-gray-700 dark:text-gray-300">{row.invoiceCount}</td>
                  <td className="text-right py-2 font-medium text-gray-900 dark:text-gray-100">{fmt(row.totalGross)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
