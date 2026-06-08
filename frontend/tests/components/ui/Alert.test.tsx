import { screen } from '@testing-library/react';
import { Alert } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('Alert', () => {
  it('announces its content via role=alert', () => {
    renderWithRouter(<Alert>Heads up</Alert>);
    expect(screen.getByRole('alert')).toHaveTextContent('Heads up');
  });

  it.each([
    ['danger', 'bg-error-soft'],
    ['warning', 'bg-warning-soft'],
    ['info', 'bg-info-soft'],
    ['success', 'bg-success-soft'],
  ] as const)('applies the %s variant classes', (variant, expectedClass) => {
    renderWithRouter(<Alert variant={variant}>Message</Alert>);
    expect(screen.getByRole('alert')).toHaveClass(expectedClass);
  });

  it.each([
    ['danger', 'lucide-circle-alert'],
    ['warning', 'lucide-triangle-alert'],
    ['info', 'lucide-info'],
    ['success', 'lucide-circle-check-big'],
  ] as const)('renders the auto icon for the %s variant', (variant, iconClass) => {
    const { container } = renderWithRouter(<Alert variant={variant}>Message</Alert>);
    expect(container.querySelector(`.${iconClass}`)).toBeInTheDocument();
  });

  it('hides the icon when icon is false', () => {
    const { container } = renderWithRouter(
      <Alert variant="info" icon={false}>
        Message
      </Alert>,
    );
    expect(container.querySelector('svg')).not.toBeInTheDocument();
  });

  it('applies a custom className alongside the variant classes', () => {
    renderWithRouter(<Alert className="custom-alert">Message</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('custom-alert');
  });
});
