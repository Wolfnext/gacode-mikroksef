describe('Login Page', () => {
  beforeEach(() => {
    cy.mockApi();
    cy.visit('/login');
  });

  it('displays login form', () => {
    cy.contains('Zaloguj się do KSeF').should('be.visible');
    cy.get('input[id="nip"]').should('be.visible');
    cy.get('button[type="submit"]').should('be.visible');
    cy.contains('Środowisko testowe').should('be.visible');
  });

  it('validates NIP input', () => {
    cy.get('input[id="nip"]').type('123');
    cy.get('button[type="submit"]').should('be.disabled');

    cy.get('input[id="nip"]').clear().type('1234567890');
    cy.get('button[type="submit"]').should('not.be.disabled');
  });

  it('shows NIP character count', () => {
    cy.get('input[id="nip"]').type('12345');
    cy.contains('5/10 cyfr').should('be.visible');

    cy.get('input[id="nip"]').type('67890');
    cy.contains('10/10 cyfr').should('be.visible');
  });

  it('formats NIP with dashes', () => {
    cy.get('input[id="nip"]').type('526-025-11-09');
    // The input should accept formatted NIP
    cy.get('input[id="nip"]').should('have.value', '526-025-11-09');
  });

  it('successful login redirects to dashboard', () => {
    // Update mock to return session on status check
    cy.intercept('GET', '/api/auth/session/status', {
      statusCode: 200,
      body: {
        referenceNumber: '20260203-TEST-REF-001',
        processingCode: 200,
        processingDescription: 'Active',
        numberOfElements: 0,
        timestamp: new Date().toISOString(),
        isActive: true,
      },
    });

    cy.get('input[id="nip"]').type('5260251109');
    cy.get('button[type="submit"]').click();

    cy.wait('@sessionInit');
    cy.url().should('include', '/dashboard');
  });

  it('shows error on failed login', () => {
    cy.intercept('POST', '/api/auth/session/init-token', {
      statusCode: 401,
      body: { detail: 'Authentication failed' },
    });

    cy.get('input[id="nip"]').type('1234567890');
    cy.get('button[type="submit"]').click();

    cy.contains('Authentication failed').should('be.visible');
  });

  it('shows loading state during login', () => {
    cy.intercept('POST', '/api/auth/session/init-token', {
      delay: 1000,
      statusCode: 201,
      body: {
        sessionToken: 'test-token',
        referenceNumber: '20260203-TEST-REF-001',
        timestamp: new Date().toISOString(),
      },
    });

    cy.get('input[id="nip"]').type('1234567890');
    cy.get('button[type="submit"]').click();

    cy.get('button[type="submit"]').should('be.disabled');
    cy.get('svg.animate-spin').should('be.visible');
  });
});
