// Support file for Cypress E2E tests
// This file is run before each spec file

// Example custom command
Cypress.Commands.add('visitHost', (hostname) => {
  cy.visit(`http://${hostname}`, { failOnStatusCode: false });
});

// Handle uncaught exceptions
Cypress.on('uncaught:exception', (err, runnable) => {
  // Ignore network-related errors in CI environment
  if (err.message.includes('Failed to fetch')) {
    return false;
  }
  return true;
});
