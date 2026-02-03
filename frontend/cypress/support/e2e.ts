// Cypress support file
// Add custom commands and global configuration

// Import commands
import './commands';

// Prevent uncaught exceptions from failing tests
Cypress.on('uncaught:exception', (err, runnable) => {
  // Return false to prevent test failure
  return false;
});
