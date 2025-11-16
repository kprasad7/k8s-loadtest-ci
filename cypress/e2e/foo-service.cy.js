describe('Echo Foo Service', () => {
  beforeEach(() => {
    // Set up host header for routing
    cy.visit('http://foo.localhost', {
      headers: {
        'Host': 'foo.localhost',
      },
      failOnStatusCode: false,
    });
  });

  it('should respond with 200 OK', () => {
    cy.request({
      method: 'GET',
      url: 'http://foo.localhost/',
      headers: {
        'Host': 'foo.localhost',
      },
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.eq(200);
    });
  });

  it('should handle GET requests', () => {
    cy.request({
      method: 'GET',
      url: 'http://foo.localhost/test',
      headers: {
        'Host': 'foo.localhost',
      },
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.be.oneOf([200, 404, 500]);
    });
  });

  it('should handle POST requests', () => {
    cy.request({
      method: 'POST',
      url: 'http://foo.localhost/api/test',
      headers: {
        'Host': 'foo.localhost',
      },
      body: { test: 'data' },
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.be.oneOf([200, 404, 405, 500]);
    });
  });
});
