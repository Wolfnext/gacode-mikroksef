// Custom Cypress commands

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Login with NIP
       */
      login(nip: string): Chainable<void>;

      /**
       * Mock API responses
       */
      mockApi(): Chainable<void>;

      /**
       * Wait for page to load
       */
      waitForPage(): Chainable<void>;
    }
  }
}

// Login command
Cypress.Commands.add('login', (nip: string) => {
  cy.visit('/login');
  cy.get('input[id="nip"]').type(nip);
  cy.get('button[type="submit"]').click();
  cy.url().should('include', '/dashboard');
});

// Mock API command
Cypress.Commands.add('mockApi', () => {
  // Mock health check
  cy.intercept('GET', '/api/health', {
    statusCode: 200,
    body: {
      status: 'healthy',
      environment: 'test',
      ksefApi: 'https://ksef-test.mf.gov.pl/api',
      sessionActive: false,
      version: '1.0.0',
    },
  }).as('healthCheck');

  // Mock session status (no session)
  cy.intercept('GET', '/api/auth/session/status', {
    statusCode: 404,
    body: { detail: 'No active session' },
  }).as('sessionStatus');

  // Mock session init
  cy.intercept('POST', '/api/auth/session/init-token', {
    statusCode: 201,
    body: {
      sessionToken: 'test-token',
      referenceNumber: '20260203-TEST-REF-001',
      timestamp: new Date().toISOString(),
    },
  }).as('sessionInit');

  // Mock session status (with session)
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
  }).as('sessionStatusActive');

  // Mock invoices list
  cy.intercept('GET', '/api/invoices*', {
    statusCode: 200,
    body: {
      timestamp: new Date().toISOString(),
      referenceNumber: 'cache',
      numberOfElements: 2,
      pageSize: 50,
      pageOffset: 0,
      hasMore: false,
      invoiceHeaderList: [
        {
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
      ],
    },
  }).as('invoicesList');

  // Mock sync status
  cy.intercept('GET', '/api/sync/status*', {
    statusCode: 200,
    body: {
      status: 'never_synced',
      syncType: 'subject1',
      message: 'No sync has been performed yet',
    },
  }).as('syncStatus');
});

// Wait for page to load
Cypress.Commands.add('waitForPage', () => {
  cy.get('body').should('be.visible');
  cy.wait(500);
});

export {};
