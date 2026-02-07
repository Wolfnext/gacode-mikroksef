import './polyfills.js';

import express from 'express';
import { generateInvoice, generatePDFUPO } from '@akmf/ksef-fe-invoice-converter';

const app = express();
const PORT = parseInt(process.env.PORT || '3001', 10);

// Accept raw XML body up to 10MB
app.use(express.raw({ type: 'application/xml', limit: '10mb' }));

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'pdf-generator' });
});

// Generate invoice PDF from XML
app.post('/generate-invoice', async (req, res) => {
  try {
    const xmlBuffer: Buffer = req.body;
    if (!xmlBuffer || xmlBuffer.length === 0) {
      res.status(400).json({ error: 'XML body required' });
      return;
    }

    const nrKSeF = (req.headers['x-ksef-reference'] as string) || '';
    const qrCode = (req.headers['x-qr-code'] as string) || undefined;

    // Convert Buffer to Uint8Array for File constructor compatibility
    const xmlData = new Uint8Array(xmlBuffer);
    const file = new File([xmlData], 'invoice.xml', { type: 'application/xml' });

    const pdfBlob = await generateInvoice(
      file,
      { nrKSeF, qrCode, isMobile: false },
      'blob'
    );
    const arrayBuffer = await pdfBlob.arrayBuffer();

    res.set('Content-Type', 'application/pdf');
    res.set('Content-Disposition', `attachment; filename="${nrKSeF || 'invoice'}.pdf"`);
    res.send(Buffer.from(arrayBuffer));
  } catch (error) {
    console.error('PDF generation failed:', error);
    res.status(500).json({ error: 'PDF generation failed', details: String(error) });
  }
});

// Generate UPO PDF from XML
app.post('/generate-upo', async (req, res) => {
  try {
    const xmlBuffer: Buffer = req.body;
    if (!xmlBuffer || xmlBuffer.length === 0) {
      res.status(400).json({ error: 'XML body required' });
      return;
    }

    const nrKSeF = (req.headers['x-ksef-reference'] as string) || 'UPO';

    const xmlData = new Uint8Array(xmlBuffer);
    const file = new File([xmlData], 'upo.xml', { type: 'application/xml' });

    const pdfBlob = await generatePDFUPO(file);
    const arrayBuffer = await pdfBlob.arrayBuffer();

    res.set('Content-Type', 'application/pdf');
    res.set('Content-Disposition', `attachment; filename="UPO_${nrKSeF}.pdf"`);
    res.send(Buffer.from(arrayBuffer));
  } catch (error) {
    console.error('UPO PDF generation failed:', error);
    res.status(500).json({ error: 'UPO PDF generation failed', details: String(error) });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`PDF Generator service running on port ${PORT}`);
});
