declare module '@akmf/ksef-fe-invoice-converter' {
  interface AdditionalDataTypes {
    nrKSeF: string;
    qrCode?: string;
    isMobile?: boolean;
  }

  export function generateInvoice(
    file: File,
    additionalData: AdditionalDataTypes,
    formatType: 'blob'
  ): Promise<Blob>;

  export function generateInvoice(
    file: File,
    additionalData: AdditionalDataTypes,
    formatType: 'base64'
  ): Promise<string>;

  export function generatePDFUPO(file: File): Promise<Blob>;
}
