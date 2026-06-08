import { screen } from '@testing-library/react';
import { LoadingState } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('LoadingState', () => {
  it('exposes a status role for assistive tech', () => {
    renderWithRouter(<LoadingState />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows the default loading label', () => {
    renderWithRouter(<LoadingState />);
    expect(screen.getByText('Loading…')).toBeInTheDocument();
  });

  it('shows a custom label', () => {
    renderWithRouter(<LoadingState label="Fetching items…" />);
    expect(screen.getByText('Fetching items…')).toBeInTheDocument();
  });
});
