import { screen } from '@testing-library/react';
import NotFound from '~/routes/not-found';
import { createRouteStub } from '../utils/createStub';

function renderNotFound(): void {
  createRouteStub([{ path: '/', Component: NotFound }]);
}

describe('not-found route', () => {
  it('renders a page-not-found heading', () => {
    renderNotFound();
    expect(screen.getByRole('heading', { name: /page not found/i })).toBeInTheDocument();
  });

  it('links back to the home page', () => {
    renderNotFound();
    expect(screen.getByRole('link', { name: /back to home/i })).toHaveAttribute('href', '/');
  });
});
