/**
 * KSeF Invoice XML Parser
 * Parses FA(3) invoice XML structure to extract invoice data including line items.
 */

import type { ParsedInvoice, InvoiceLineItem } from '@/types';

/**
 * Get text content of an XML element by tag name.
 */
function getElementText(parent: Element | Document, tagName: string): string | undefined {
  // Try with namespace prefix first (common patterns)
  const prefixes = ['', 'tns:', 'fa:'];
  for (const prefix of prefixes) {
    const elements = parent.getElementsByTagName(prefix + tagName);
    if (elements.length > 0 && elements[0].textContent) {
      return elements[0].textContent.trim();
    }
  }
  return undefined;
}

/**
 * Get all elements by tag name.
 */
function getElements(parent: Element | Document, tagName: string): Element[] {
  const prefixes = ['', 'tns:', 'fa:'];
  for (const prefix of prefixes) {
    const elements = parent.getElementsByTagName(prefix + tagName);
    if (elements.length > 0) {
      return Array.from(elements);
    }
  }
  return [];
}

/**
 * Parse numeric value from string.
 */
function parseNumber(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const num = parseFloat(value.replace(',', '.'));
  return isNaN(num) ? undefined : num;
}

/**
 * Parse a single invoice line item (FaWiersz).
 */
function parseLineItem(element: Element, index: number): InvoiceLineItem {
  return {
    lineNumber: parseNumber(getElementText(element, 'NrWierszaFa')) || index + 1,
    name: getElementText(element, 'P_7') || getElementText(element, 'NazwaTowaru') || 'Pozycja bez nazwy',
    description: getElementText(element, 'P_7Z') || getElementText(element, 'OpisTowaru'),
    quantity: parseNumber(getElementText(element, 'P_8B') || getElementText(element, 'Ilosc')),
    unit: getElementText(element, 'P_8A') || getElementText(element, 'Jednostka'),
    unitPriceNet: parseNumber(getElementText(element, 'P_9A') || getElementText(element, 'CenaJednostkowa')),
    netValue: parseNumber(getElementText(element, 'P_11') || getElementText(element, 'WartoscNetto')) || 0,
    vatRate: getElementText(element, 'P_12') || getElementText(element, 'StawkaVAT'),
    vatAmount: parseNumber(getElementText(element, 'P_11Vat')),
    grossValue: parseNumber(getElementText(element, 'P_11Brutto')),
    pkwiu: getElementText(element, 'PKWiU'),
    gtin: getElementText(element, 'GTIN'),
    cn: getElementText(element, 'CN'),
  };
}

/**
 * Parse address from XML element.
 */
function parseAddress(element: Element | undefined): { address?: string; city?: string; postalCode?: string; country?: string } {
  if (!element) return {};

  return {
    address: getElementText(element, 'Ulica') || getElementText(element, 'AdresL1'),
    city: getElementText(element, 'Miejscowosc') || getElementText(element, 'AdresL2'),
    postalCode: getElementText(element, 'KodPocztowy'),
    country: getElementText(element, 'KodKraju') || 'PL',
  };
}

/**
 * Parse seller data from XML.
 */
function parseSeller(doc: Document): ParsedInvoice['seller'] {
  const podmiot1 = getElements(doc, 'Podmiot1')[0];
  if (!podmiot1) return undefined;

  const daneId = getElements(podmiot1, 'DaneIdentyfikacyjne')[0] || podmiot1;
  const adres = getElements(podmiot1, 'Adres')[0];

  return {
    name: getElementText(daneId, 'Nazwa') || getElementText(daneId, 'PelnaNazwa'),
    tradeName: getElementText(daneId, 'NazwaHandlowa'),
    nip: getElementText(daneId, 'NIP'),
    ...parseAddress(adres),
  };
}

/**
 * Parse buyer data from XML.
 */
function parseBuyer(doc: Document): ParsedInvoice['buyer'] {
  const podmiot2 = getElements(doc, 'Podmiot2')[0];
  if (!podmiot2) return undefined;

  const daneId = getElements(podmiot2, 'DaneIdentyfikacyjne')[0] || podmiot2;
  const adres = getElements(podmiot2, 'Adres')[0];

  return {
    name: getElementText(daneId, 'Nazwa') || getElementText(daneId, 'PelnaNazwa'),
    tradeName: getElementText(daneId, 'NazwaHandlowa'),
    nip: getElementText(daneId, 'NIP'),
    ...parseAddress(adres),
  };
}

/**
 * Parse VAT summary from XML.
 */
function parseVatSummary(doc: Document): ParsedInvoice['vatSummary'] {
  const summaryElements = getElements(doc, 'P_13_');
  if (summaryElements.length === 0) return undefined;

  const summary: ParsedInvoice['vatSummary'] = [];

  // Try to find all rate-specific summary elements
  const rates = ['23', '22', '8', '7', '5', '4', '0', 'zw', 'np', 'oo'];

  for (const rate of rates) {
    const netElement = getElementText(doc, `P_13_${rate}`) || getElementText(doc, `P13_${rate}`);
    const vatElement = getElementText(doc, `P_14_${rate}`) || getElementText(doc, `P14_${rate}`);

    const netValue = parseNumber(netElement);
    const vatValue = parseNumber(vatElement);

    if (netValue !== undefined || vatValue !== undefined) {
      summary.push({
        rate: rate === 'zw' ? 'zw.' : rate === 'np' ? 'np.' : rate === 'oo' ? 'o.o.' : `${rate}%`,
        netValue: netValue || 0,
        vatValue: vatValue || 0,
      });
    }
  }

  return summary.length > 0 ? summary : undefined;
}

/**
 * Parse KSeF FA(3) invoice XML to structured data.
 */
export function parseInvoiceXml(xmlContent: string): ParsedInvoice | null {
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlContent, 'text/xml');

    // Check for parse errors
    const parseError = doc.querySelector('parsererror');
    if (parseError) {
      console.error('XML parse error:', parseError.textContent);
      return null;
    }

    // Parse line items (FaWiersz)
    const lineItemElements = getElements(doc, 'FaWiersz');
    const items: InvoiceLineItem[] = lineItemElements.map((el, idx) => parseLineItem(el, idx));

    // Parse control summary (FaWierszCtrl)
    const ctrl = getElements(doc, 'FaWierszCtrl')[0];
    const itemsCount = parseNumber(getElementText(ctrl || doc, 'LiczbaWierszyFaktury'));
    const itemsTotalNet = parseNumber(getElementText(ctrl || doc, 'WartoscWierszyFaktury'));

    // Parse totals
    const totalNet = parseNumber(getElementText(doc, 'P_13_1')) ||
                     parseNumber(getElementText(doc, 'RazemNetto')) ||
                     itemsTotalNet;
    const totalVat = parseNumber(getElementText(doc, 'P_14_1')) ||
                     parseNumber(getElementText(doc, 'RazemVAT'));
    const totalGross = parseNumber(getElementText(doc, 'P_15')) ||
                       parseNumber(getElementText(doc, 'RazemBrutto'));

    return {
      // Header
      invoiceNumber: getElementText(doc, 'P_2') || getElementText(doc, 'NrFaktury'),
      issueDate: getElementText(doc, 'P_1') || getElementText(doc, 'DataWystawienia'),
      saleDate: getElementText(doc, 'P_6') || getElementText(doc, 'DataSprzedazy'),
      currency: getElementText(doc, 'KodWaluty') || 'PLN',

      // Parties
      seller: parseSeller(doc),
      buyer: parseBuyer(doc),

      // Items
      items,
      itemsCount,
      itemsTotalNet,

      // VAT summary
      vatSummary: parseVatSummary(doc),

      // Totals
      totalNet,
      totalVat,
      totalGross,

      // Payment
      paymentMethod: getElementText(doc, 'FormaPlatnosci') || getElementText(doc, 'P_19'),
      paymentDueDate: getElementText(doc, 'TerminPlatnosci') || getElementText(doc, 'P_19A'),
      bankAccount: getElementText(doc, 'NrRachunku') || getElementText(doc, 'RachunekBankowy'),

      // Notes
      notes: getElementText(doc, 'Uwagi') || getElementText(doc, 'DodatkoweInfo'),
    };
  } catch (error) {
    console.error('Failed to parse invoice XML:', error);
    return null;
  }
}
