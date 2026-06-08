import { screen, fireEvent } from '@testing-library/react';
import { Table } from '~/components/ui';
import type { Column } from '~/components/ui';
import type { Item } from '~/types';
import { buildItems, mockItems } from '../../mocks';
import { renderWithRouter } from '../../utils/render';
import { createRouteStub } from '../../utils/createStub';

const columns: Column<Item>[] = [
  { header: 'Name', cell: (row) => row.name, sortKey: 'name' },
  { header: 'Status', cell: (row) => row.status },
];

describe('Table', () => {
  it('renders a row for each item using the column cells', () => {
    renderWithRouter(<Table columns={columns} rows={mockItems} />);
    expect(screen.getByText('First item')).toBeInTheDocument();
    expect(screen.getByText('Second item')).toBeInTheDocument();
    expect(screen.getByText('Third item')).toBeInTheDocument();
  });

  it('renders the column headers', () => {
    renderWithRouter(<Table columns={columns} rows={mockItems} />);
    expect(screen.getByRole('columnheader', { name: 'Name' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Status' })).toBeInTheDocument();
  });

  it('shows the empty message when there are no rows', () => {
    renderWithRouter(<Table columns={columns} rows={[]} emptyMessage="No items found" />);
    expect(screen.getByText('No items found')).toBeInTheDocument();
  });

  it('marks the active sort column with aria-sort ascending', () => {
    renderWithRouter(
      <Table
        columns={columns}
        rows={mockItems}
        sort={{ orderBy: 'name', orderDirection: 'asc' }}
        onSortChange={jest.fn()}
      />,
    );
    expect(screen.getByRole('columnheader', { name: /Name/ })).toHaveAttribute(
      'aria-sort',
      'ascending',
    );
  });

  it('marks the active sort column with aria-sort descending', () => {
    renderWithRouter(
      <Table
        columns={columns}
        rows={mockItems}
        sort={{ orderBy: 'name', orderDirection: 'desc' }}
        onSortChange={jest.fn()}
      />,
    );
    expect(screen.getByRole('columnheader', { name: /Name/ })).toHaveAttribute(
      'aria-sort',
      'descending',
    );
  });

  it('calls onSortChange with the column sortKey when a sortable header is activated', () => {
    const onSortChange = jest.fn();
    renderWithRouter(
      <Table columns={columns} rows={mockItems} sort={{}} onSortChange={onSortChange} />,
    );
    fireEvent.click(screen.getByRole('button', { name: /Name/ }));
    expect(onSortChange).toHaveBeenCalledWith('name');
  });

  it('navigates to the row href when a navigable row is clicked', async () => {
    createRouteStub(
      [
        {
          path: '/items',
          Component: () => (
            <Table
              columns={columns}
              rows={[mockItems[0]]}
              getRowHref={(row) => `/items/${row.id}`}
            />
          ),
        },
        { path: '/items/1', Component: () => <p>Item detail</p> },
      ],
      { initialPath: '/items' },
    );
    fireEvent.click(screen.getByRole('link'));
    expect(await screen.findByText('Item detail')).toBeInTheDocument();
  });

  it('navigates to the row href when Enter is pressed on a navigable row', async () => {
    createRouteStub(
      [
        {
          path: '/items',
          Component: () => (
            <Table
              columns={columns}
              rows={[mockItems[0]]}
              getRowHref={(row) => `/items/${row.id}`}
            />
          ),
        },
        { path: '/items/1', Component: () => <p>Item detail</p> },
      ],
      { initialPath: '/items' },
    );
    fireEvent.keyDown(screen.getByRole('link'), { key: 'Enter' });
    expect(await screen.findByText('Item detail')).toBeInTheDocument();
  });

  it('embeds pagination when total spans more than one page', () => {
    renderWithRouter(
      <Table columns={columns} rows={buildItems(20)} total={60} page={1} pageSize={20} />,
    );
    expect(screen.getByRole('navigation', { name: 'Pagination' })).toBeInTheDocument();
  });
});
