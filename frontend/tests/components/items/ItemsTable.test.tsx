import { screen, within } from '@testing-library/react';
import { ItemsTable } from '~/components/items/ItemsTable';
import { renderWithRouter } from '../../utils/render';
import { mockItems } from '../../mocks';

describe('ItemsTable', () => {
  it('renders the column headers', () => {
    renderWithRouter(<ItemsTable items={mockItems} />);
    expect(screen.getByRole('columnheader', { name: /name/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /description/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /category/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /status/i })).toBeInTheDocument();
  });

  it('renders the name, description, category and status for a row', () => {
    renderWithRouter(<ItemsTable items={[mockItems[0]]} />);
    const row = screen.getByRole('link', { name: /First item/ });
    expect(within(row).getByText('First item')).toBeInTheDocument();
    expect(within(row).getByText('A representative item used across tests.')).toBeInTheDocument();
    expect(within(row).getByText('general')).toBeInTheDocument();
    expect(within(row).getByText('Active')).toBeInTheDocument();
  });

  it('renders an em dash when a row has no category', () => {
    renderWithRouter(<ItemsTable items={[mockItems[1]]} />);
    const row = screen.getByRole('link', { name: /Second item/ });
    expect(within(row).getByText('—')).toBeInTheDocument();
  });

  it('renders a navigable row per item', () => {
    renderWithRouter(<ItemsTable items={mockItems} />);
    expect(screen.getAllByRole('link')).toHaveLength(mockItems.length);
  });

  it('renders the empty message when there are no items', () => {
    renderWithRouter(<ItemsTable items={[]} emptyMessage="No items yet." />);
    expect(screen.getByText('No items yet.')).toBeInTheDocument();
  });
});
