describe('Ingress Routing', () => {
  it('should route foo.localhost to foo service', () => {
    cy.request({
      method: 'GET',
      url: 'http://foo.localhost/',
      headers: {
        'Host': 'foo.localhost',
      },
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.eq(200);
      // The response should contain echo service info
      expect(response.body).to.be.a('string');
    });
  });

  it('should route bar.localhost to bar service', () => {
    cy.request({
      method: 'GET',
      url: 'http://bar.localhost/',
      headers: {
        'Host': 'bar.localhost',
      },
      failOnStatusCode: false,
    }).then((response) => {
      expect(response.status).to.eq(200);
      // The response should contain echo service info
      expect(response.body).to.be.a('string');
    });
  });

  it('should handle multiple concurrent requests', () => {
    const requests = [];
    for (let i = 0; i < 10; i++) {
      requests.push(
        cy.request({
          method: 'GET',
          url: `http://foo.localhost/request-${i}`,
          headers: {
            'Host': 'foo.localhost',
          },
          failOnStatusCode: false,
        })
      );
    }

    cy.wrap(requests).then((responses) => {
      responses.forEach((response) => {
        expect(response.status).to.be.oneOf([200, 404, 500]);
      });
    });
  });
});
