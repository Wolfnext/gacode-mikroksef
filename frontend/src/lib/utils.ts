/**
 * Utility functions for the frontend.
 */

/**
 * Format currency value in PLN.
 */
export function formatCurrency(value: string | number, currency = 'PLN'): string {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  return new Intl.NumberFormat('pl-PL', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numValue);
}

/**
 * Format date in Polish locale.
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('pl-PL', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
}

/**
 * Format datetime in Polish locale.
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('pl-PL', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

/**
 * Format NIP with dashes (XXX-XXX-XX-XX).
 */
export function formatNip(nip: string): string {
  const cleaned = nip.replace(/\D/g, '');
  if (cleaned.length !== 10) return nip;
  return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 6)}-${cleaned.slice(6, 8)}-${cleaned.slice(8)}`;
}

/**
 * Clean NIP (remove dashes and spaces).
 */
export function cleanNip(nip: string): string {
  return nip.replace(/[\s-]/g, '');
}

/**
 * Validate NIP format.
 */
export function isValidNip(nip: string): boolean {
  const cleaned = cleanNip(nip);
  if (cleaned.length !== 10 || !/^\d+$/.test(cleaned)) return false;

  // NIP checksum validation
  const weights = [6, 5, 7, 2, 3, 4, 5, 6, 7];
  let sum = 0;

  for (let i = 0; i < 9; i++) {
    sum += parseInt(cleaned[i], 10) * weights[i];
  }

  const checksum = sum % 11;
  return checksum === parseInt(cleaned[9], 10) && checksum !== 10;
}

/**
 * Truncate KSeF reference number for display.
 */
export function truncateKsefRef(ref: string, maxLength = 25): string {
  if (ref.length <= maxLength) return ref;
  return `${ref.slice(0, maxLength)}...`;
}

/**
 * Get invoice type label.
 */
export function getInvoiceTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    VAT: 'Faktura VAT',
    KOR: 'Korekta',
    ZAL: 'Zaliczkowa',
    ROZ: 'Rozliczeniowa',
  };
  return labels[type] || type;
}

/**
 * Get invoice type badge color.
 */
export function getInvoiceTypeBadgeColor(type: string): string {
  const colors: Record<string, string> = {
    VAT: 'bg-blue-100 text-blue-800',
    KOR: 'bg-yellow-100 text-yellow-800',
    ZAL: 'bg-green-100 text-green-800',
    ROZ: 'bg-purple-100 text-purple-800',
  };
  return colors[type] || 'bg-gray-100 text-gray-800';
}

/**
 * Download blob as file.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Get relative time string.
 */
export function getRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'przed chwilą';
  if (diffMins < 60) return `${diffMins} min temu`;
  if (diffHours < 24) return `${diffHours} godz. temu`;
  if (diffDays < 7) return `${diffDays} dni temu`;

  return formatDate(dateString);
}
