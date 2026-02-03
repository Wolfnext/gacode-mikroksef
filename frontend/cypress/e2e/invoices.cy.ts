describe('Invoices Page', () => {
  beforeEach(() => {
    cy.mockApi();

    // Mock active session
    cy.intercept('GET', '/api/auth/session/status', {
      statusCode: 200,
      body: {
        referenceNumber: '20260203-TEST-REF-001',
        processingCode: 200,
        processingDescription: 'Active',
        numberOfElements: 5,
        timestamp: new Date().toISOString(),
        isActive: true,
      },
    });

    // Mock invoices list
    cy.fixture('invoices').then((invoices) => {
      cy.intercept('GET', '/api/invoices*', {
        statusCode: 200,
        body: invoices.list,
      }).as('invoicesList');
    });

    cy.visit('/invoices');
  });

  it('displays invoice list', () => {
    cy.wait('@invoicesList');
    cy.contains('Faktury').should('be.visible');
    cy.get('table').should('be.visible');
  });

  it('shows invoice data in table', () => {
    cy.wait('@invoicesList');

    // Check table headers
    cy.contains('th', 'Numer KSeF').should('be.visible');
    cy.contains('th', 'Data').should('be.visible');
    cy.contains('th', 'Netto').should('be.visible');
    cy.contains('th', 'VAT').should('be.visible');
    cy.contains('th', 'Brutto').should('be.visible');

    // Check invoice data
    cy.contains('1234567890-20260203-ABC').should('be.visible');
    cy.contains('Client Company S.A.').should('be.visible');
    cy.contains('1 230,00').should('be.visible'); // Gross amount in PLN format
  });

  it('can switch between issued and received', () => {
    cy.get('select').first().select('subject2');
    cy.wait('@invoicesList');
    cy.contains('Otrzymane').should('be.visible');
  });

  it('can toggle filters panel', () => {
    cy.contains('button', 'Filtry').click();
    cy.contains('label', 'Data od').should('be.visible');
    cy.contains('label', 'Data do').should('be.visible');
    cy.contains('label', 'NIP kontrahenta').should('be.visible');
    cy.contains('label', 'Typ faktury').should('be.visible');
  });

  it('can apply date filters', () => {
    cy.contains('button', 'Filtry').click();
    cy.get('input[type="date"]').first().type('2026-01-01');
    cy.get('input[type="date"]').last().type('2026-12-31');
    cy.contains('button', 'Zastosuj filtry').click();
    cy.wait('@invoicesList');
  });

  it('shows pagination info', () => {
    cy.wait('@invoicesList');
    cy.contains('Wyświetlono 1 - 3 z 3 faktur').should('be.visible');
  });

  it('can navigate to invoice detail', () => {
    cy.wait('@invoicesList');

    // Mock invoice detail
    cy.intercept('GET', '/api/invoices/1234567890-20260203-ABC123-XY', {
      statusCode: 200,
      body: {
        header: {
          invoiceReferenceNumber: 'FV/2026/001',
          ksefReferenceNumber: '1234567890-20260203-ABC123-XY',
          invoicingDate: '2026-02-01',
          acquisitionTimestamp: new Date().toISOString(),
          subjectBy: {
            identifierType: 'nip',
            identifier: '1234567890',
            name: 'Test Company Sp. z o.o.',
          },
          subjectTo: {
            identifierType: 'nip',
            identifier: '0987654321',
            name: 'Client Company S.A.',
          },
          net: '1000.00',
          vat: '230.00',
          gross: '1230.00',
          currency: 'PLN',
          invoiceType: 'VAT',
        },
        xmlContent: '<?xml version="1.0"?><Invoice/>',
        upoAvailable: false,
      },
    });

    cy.get('table tbody tr').first().within(() => {
      cy.get('a').first().click();
    });

    cy.url().should('include', '/invoices/');
  });

  it('can sync invoices', () => {
    cy.intercept('POST', '/api/sync/issued*', {
      statusCode: 200,
      body: {
        status: 'completed',
        totalFetched: 10,
        newInvoices: 5,
        updatedInvoices: 5,
        errors: [],
        startedAt: new Date().toISOString(),
        completedAt: new Date().toISOString(),
      },
    }).as('sync');

    cy.contains('button', 'Synchronizuj').click();
    cy.wait('@sync');
  });

  it('shows invoice type badges', () => {
    cy.wait('@invoicesList');
    cy.contains('Faktura VAT').should('be.visible');
    cy.contains('Korekta').should('be.visible');
  });
});

describe('Invoices - Empty State', () => {
  beforeEach(() => {
    cy.mockApi();

    cy.intercept('GET', '/api/auth/session/status', {
      statusCode: 200,
      body: {
        referenceNumber: '20260203-TEST-REF-001',
        processingCode: 200,
        isActive: true,
      },
    });

    cy.fixture('invoices').then((invoices) => {
      cy.intercept('GET', '/api/invoices*', {
        statusCode: 200,
        body: invoices.empty,
      });
    });

    cy.visit('/invoices');
  });

  it('shows empty state message', () => {
    cy.contains('Brak faktur do wyświetlenia').should('be.visible');
    cy.contains('Synchronizuj').should('be.visible');
  });
});
