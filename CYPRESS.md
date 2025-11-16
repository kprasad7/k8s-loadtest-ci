# Cypress E2E Tests Configuration

Cypress end-to-end tests for validating the Kubernetes load test CI infrastructure.

## Overview

The Cypress test suite provides automated testing of:

- **Service Routing**: Validates that ingress properly routes `foo.localhost` and `bar.localhost` to their respective services
- **Health Checks**: Ensures services respond with appropriate HTTP status codes
- **API Endpoints**: Tests GET and POST request handling
- **Concurrency**: Verifies services can handle multiple concurrent requests
- **Integration**: Tests the complete request flow through the ingress controller

## Test Files

### `cypress/e2e/foo-service.cy.js`
Tests for the Echo Foo service:
- 200 OK response validation
- GET request handling
- POST request handling

### `cypress/e2e/bar-service.cy.js`
Tests for the Echo Bar service:
- 200 OK response validation  
- GET request handling
- POST request handling

### `cypress/e2e/ingress-routing.cy.js`
Tests for ingress functionality:
- Host-based routing to foo service
- Host-based routing to bar service
- Concurrent request handling

## Running Tests Locally

### Prerequisites
```bash
npm install -g cypress
```

### Run All Tests
```bash
cypress run
```

### Run Tests in Headed Mode (with browser)
```bash
cypress open
```

### Run Specific Test File
```bash
cypress run --spec "cypress/e2e/foo-service.cy.js"
```

### Run with Python Script
```bash
python scripts/run_cypress_tests.py
```

## CI Integration

Tests are automatically run as part of the GitHub Actions workflow:

1. **After health checks** - Ensures services are ready before testing
2. **Before load tests** - Validates basic functionality before stress testing
3. **Results uploaded** - Test results included in PR comments and artifacts

## Test Configuration

Configuration is defined in `cypress.config.js`:

- **Base URL**: `http://localhost:8000` (during CI, services are accessed via ingress)
- **Viewport**: 1280x720
- **Video Recording**: Enabled
- **Screenshots**: Captured on failure
- **Timeout**: 5 minutes per test suite

## Debugging Failed Tests

### View Videos/Screenshots
```bash
# After running tests
open cypress/videos
open cypress/screenshots
```

### Check JSON Results
```bash
cat artifacts/cypress-results.json
cat artifacts/cypress-results.md
```

### Run with Debug Output
```bash
DEBUG=cypress:* cypress run
```

### CI Artifacts
- `artifacts/cypress-results.json` - Raw test results
- `artifacts/cypress-results.md` - Formatted test report
- Included in PR comments for quick visibility

## Common Issues

### Tests timeout in CI
- Increase timeout in `cypress.config.js`
- Ensure health checks pass before running tests
- Verify ingress controller is fully deployed

### Host routing fails
- Ensure `Host` header is set correctly in requests
- Verify /etc/hosts contains localhost entries (or use direct IP)
- Check ingress rules match hostname

### Service not responding
- Run health checks: `python scripts/check_health.py`
- Check pod logs: `kubectl logs -l app=echo-foo`
- Verify network connectivity in cluster

## Extending Tests

To add new tests:

1. Create new `.cy.js` file in `cypress/e2e/`
2. Follow the existing test structure
3. Use custom commands from `cypress/support/e2e.js`
4. Run locally to validate: `cypress run`
5. Commit and push to trigger CI

## References

- [Cypress Documentation](https://docs.cypress.io)
- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [HTTP Testing with Cypress](https://docs.cypress.io/api/commands/request)
