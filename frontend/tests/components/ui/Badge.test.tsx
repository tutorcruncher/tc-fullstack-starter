import { screen } from '@testing-library/react';
import { Badge } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('Badge', () => {
  it('renders its children', () => {
    renderWithRouter(<Badge>Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('uses the neutral variant by default', () => {
    renderWithRouter(<Badge>Default</Badge>);
    expect(screen.getByText('Default')).toHaveClass('bg-neutral-100', 'text-neutral-700');
  });

  it.each([
    ['neutral', ['bg-neutral-100', 'text-neutral-700']],
    ['primary', ['bg-primary-soft', 'text-primary-dark']],
    ['success', ['bg-success-soft', 'text-success']],
    ['warning', ['bg-warning-soft', 'text-warning']],
    ['error', ['bg-error-soft', 'text-error']],
    ['info', ['bg-info-soft', 'text-info']],
  ] as const)('applies the %s variant classes', (variant, expectedClasses) => {
    renderWithRouter(<Badge variant={variant}>Label</Badge>);
    expect(screen.getByText('Label')).toHaveClass(...expectedClasses);
  });

  it('applies a custom className alongside the variant classes', () => {
    renderWithRouter(<Badge className="custom-badge">Label</Badge>);
    expect(screen.getByText('Label')).toHaveClass('custom-badge');
  });
});
