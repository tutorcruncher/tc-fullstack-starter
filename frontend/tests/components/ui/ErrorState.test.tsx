import { screen, fireEvent } from '@testing-library/react';
import { ErrorState } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('ErrorState', () => {
  it('announces the error via role=alert', () => {
    renderWithRouter(<ErrorState message="Could not load items" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Could not load items');
  });

  it('shows the error message', () => {
    renderWithRouter(<ErrorState message="Could not load items" />);
    expect(screen.getByText('Could not load items')).toBeInTheDocument();
  });

  it('does not render a retry button when no handler is given', () => {
    renderWithRouter(<ErrorState message="Boom" />);
    expect(screen.queryByRole('button', { name: 'Try again' })).not.toBeInTheDocument();
  });

  it('renders a retry button when a handler is given', () => {
    renderWithRouter(<ErrorState message="Boom" onRetry={() => {}} />);
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
  });

  it('calls onRetry when the retry button is clicked', () => {
    const onRetry = jest.fn();
    renderWithRouter(<ErrorState message="Boom" onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
