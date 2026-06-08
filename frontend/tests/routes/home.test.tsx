import { screen } from '@testing-library/react';
import Home from '~/routes/home';
import { createRouteStub } from '../utils/createStub';

function renderHome(): void {
  createRouteStub([{ path: '/', Component: Home }]);
}

describe('home route', () => {
  it('renders a welcome heading', () => {
    renderHome();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/welcome to/i);
  });

  it('links through to the items list', () => {
    renderHome();
    expect(screen.getByRole('link', { name: /view items/i })).toHaveAttribute('href', '/items');
  });
});
