describe('Dashboard Page', () => {
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
    }).as('sessionStatus');

    cy.visit('/dashboard');
  });

  it('displays dashboard with session info', () => {
    cy.contains('Dashboard').should('be.visible');
    cy.contains('Faktury wystawione').should('be.visible');
    cy.contains('Faktury otrzymane').should('be.visible');
  });

  it('shows session status in header', () => {
    cy.get('header').within(() => {
      cy.contains('Aktywna').should('be.visible');
      cy.contains('Ref:').should('be.visible');
    });
  });

  it('has navigation links', () => {
    cy.get('header').within(() => {
      cy.contains('Dashboard').should('be.visible');
      cy.contains('Faktury').should('be.visible');
    });
  });

  it('shows sync buttons', () => {
    cy.contains('button', 'Synchronizuj').should('have.length.at.least', 2);
  });

  it('shows browse buttons', () => {
    cy.contains('button', 'Przeglądaj').should('have.length.at.least', 2);
  });

  it('can navigate to invoices page', () => {
    cy.contains('button', 'Przeglądaj').first().click();
    cy.url().should('include', '/invoices');
  });

  it('can logout', () => {
    cy.intercept('POST', '/api/auth/session/terminate', {
      statusCode: 200,
      body: { message: 'Session terminated' },
    });

    // Mock no session after logout
    cy.intercept('GET', '/api/auth/session/status', {
      statusCode: 404,
      body: { detail: 'No active session' },
    });

    cy.contains('button', 'Wyloguj').click();
    cy.url().should('include', '/login');
  });

  it('can trigger sync', () => {
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
    }).as('syncIssued');

    cy.contains('Faktury wystawione')
      .parent()
      .parent()
      .within(() => {
        cy.contains('button', 'Synchronizuj').click();
      });

    cy.wait('@syncIssued');
  });
});

describe('Dashboard - Unauthenticated', () => {
  it('redirects to login when not authenticated', () => {
    cy.intercept('GET', '/api/auth/session/status', {
      statusCode: 404,
      body: { detail: 'No active session' },
    });

    cy.visit('/dashboard');
    cy.url().should('include', '/login');
  });
});
