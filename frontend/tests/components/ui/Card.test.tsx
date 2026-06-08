import { screen } from '@testing-library/react';
import { Card } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('Card', () => {
  it('renders its children', () => {
    renderWithRouter(<Card>Panel body</Card>);
    expect(screen.getByText('Panel body')).toBeInTheDocument();
  });

  it('uses the default white background', () => {
    renderWithRouter(<Card>Body</Card>);
    expect(screen.getByText('Body')).toHaveClass('bg-white');
  });

  it('overrides the background with bgClassName', () => {
    renderWithRouter(<Card bgClassName="bg-neutral-50">Body</Card>);
    const card = screen.getByText('Body');
    expect(card).toHaveClass('bg-neutral-50');
    expect(card).not.toHaveClass('bg-white');
  });

  it('adds the hover background utility when hover is set', () => {
    renderWithRouter(<Card hover>Body</Card>);
    expect(screen.getByText('Body')).toHaveClass('hover:bg-neutral-50');
  });

  it('omits the hover background utility by default', () => {
    renderWithRouter(<Card>Body</Card>);
    expect(screen.getByText('Body')).not.toHaveClass('hover:bg-neutral-50');
  });

  it('applies a custom className', () => {
    renderWithRouter(<Card className="custom-card">Body</Card>);
    expect(screen.getByText('Body')).toHaveClass('custom-card');
  });
});
