import { screen, fireEvent } from '@testing-library/react';
import { Button } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('Button', () => {
  it('renders its children inside a native button by default', () => {
    renderWithRouter(<Button>Save</Button>);
    expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = jest.fn();
    renderWithRouter(<Button onClick={onClick}>Save</Button>);
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('exposes an accessible name via ariaLabel when there are no text children', () => {
    renderWithRouter(<Button ariaLabel="Delete" icon={<span aria-hidden>x</span>} />);
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
  });

  it('is disabled and unclickable when disabled', () => {
    const onClick = jest.fn();
    renderWithRouter(
      <Button disabled onClick={onClick}>
        Save
      </Button>,
    );
    const button = screen.getByRole('button', { name: 'Save' });
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('renders an internal link when given an href', () => {
    renderWithRouter(<Button href="/items">Items</Button>);
    expect(screen.getByRole('link', { name: 'Items' })).toHaveAttribute('href', '/items');
  });

  it('renders an external link that opens in a new tab when targetBlank is set', () => {
    renderWithRouter(
      <Button href="https://example.com" targetBlank>
        Docs
      </Button>,
    );
    const link = screen.getByRole('link', { name: 'Docs' });
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('falls back to a native button when disabled even if an href is given', () => {
    renderWithRouter(
      <Button href="/items" disabled>
        Items
      </Button>,
    );
    expect(screen.queryByRole('link', { name: 'Items' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Items' })).toBeDisabled();
  });

  it.each([
    ['primary', 'bg-primary'],
    ['outline', 'border-neutral-200'],
    ['ghost', 'bg-transparent'],
    ['white', 'bg-white'],
  ] as const)('applies the %s variant classes', (variant, expectedClass) => {
    renderWithRouter(<Button variant={variant}>Label</Button>);
    expect(screen.getByRole('button', { name: 'Label' })).toHaveClass(expectedClass);
  });
});
