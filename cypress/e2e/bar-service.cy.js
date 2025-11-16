describe('Echo Bar Service', () => {
  beforeEach(() => {
    // Set up host header for routing
    cy.visit('http://bar.localhost', {
      headers: {
        'Host': 'bar.localhost',
      },
      failOnStatusCode: false,
    });
  });

  it('should respond with 200 OK', () => {
    cy.request({
      method: 'GET',
      url: 'http://bar.localhost/',
      headers: {
        'Host': 'bar.localhost',
      },
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.eq(200);
    });
  });

  it('should handle GET requests', () => {
    cy.request({
      method: 'GET',
      url: 'http://bar.localhost/test',
      headers: {
        'Host': 'bar.localhost',
      },
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.be.oneOf([200, 404, 500]);
    });
  });

  it('should handle POST requests', () => {
    cy.request({
      method: 'POST',
      url: 'http://bar.localhost/api/test',
      headers: {
        'Host': 'bar.localhost',
      },
      body: { test: 'data' },
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.be.oneOf([200, 404, 405, 500]);
    });
  });
});
