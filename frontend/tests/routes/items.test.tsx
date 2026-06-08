import { screen, fireEvent, waitFor, within } from '@testing-library/react';
import Items, { loader } from '~/routes/items/items';
import { itemsApi } from '~/data/api';
import type { PaginatedResponse } from '~/data/api';
import type { Item } from '~/types';
import { mockItems, buildItems } from '../mocks';
import { createRouteStub } from '../utils/createStub';

jest.mock('~/data/api', () => ({
  itemsApi: { list: jest.fn() },
}));

const mockList = jest.mocked(itemsApi.list);

function paginated(
  items: Item[],
  overrides: Partial<PaginatedResponse<Item>> = {},
): PaginatedResponse<Item> {
  return {
    items,
    total: items.length,
    page: 1,
    page_size: 20,
    ...overrides,
  };
}

function renderList(initialPath = '/items'): void {
  createRouteStub(
    [
      {
        path: '/items',
        loader,
        Component: Items,
      },
    ],
    { initialPath },
  );
}

describe('items list route', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders a row for each item returned by the loader', async () => {
    mockList.mockResolvedValue(paginated(mockItems));
    renderList();

    await waitFor(() => expect(screen.getByText('First item')).toBeInTheDocument());
    expect(screen.getByText('Second item')).toBeInTheDocument();
    expect(screen.getByText('Third item')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Items', level: 1 })).toBeInTheDocument();
  });

  it('passes the page and search params from the URL to the api', async () => {
    mockList.mockResolvedValue(paginated(mockItems, { page: 2 }));
    renderList('/items?page=2&search=widget&order_by=name&order_direction=desc');

    await waitFor(() => expect(mockList).toHaveBeenCalledTimes(1));
    expect(mockList).toHaveBeenCalledWith({
      page: 2,
      page_size: 20,
      search: 'widget',
      order_by: 'name',
      order_direction: 'desc',
    });
  });

  it('renders the empty state when there are no items', async () => {
    mockList.mockResolvedValue(paginated([]));
    renderList();

    await waitFor(() =>
      expect(screen.getByText('No items yet. Create your first one.')).toBeInTheDocument(),
    );
  });

  it('renders a search-specific empty state when a search yields nothing', async () => {
    mockList.mockResolvedValue(paginated([]));
    renderList('/items?search=nothing');

    await waitFor(() =>
      expect(screen.getByText('No items match your search.')).toBeInTheDocument(),
    );
  });

  it('reloads with the sort param when a sortable header is toggled', async () => {
    mockList.mockResolvedValue(paginated(mockItems));
    renderList();

    await waitFor(() => expect(screen.getByText('First item')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /name/i }));

    await waitFor(() => expect(mockList).toHaveBeenCalledTimes(2));
    expect(mockList).toHaveBeenLastCalledWith(
      expect.objectContaining({ order_by: 'name', order_direction: 'asc' }),
    );
  });

  it('reloads with the next page when pagination advances', async () => {
    mockList.mockResolvedValue(paginated(buildItems(20), { total: 45, page: 1 }));
    renderList();

    await waitFor(() => expect(screen.getByText('Item 1')).toBeInTheDocument());

    const pagination = screen.getByRole('navigation', { name: 'Pagination' });
    fireEvent.click(within(pagination).getByRole('button', { name: 'Next page' }));

    await waitFor(() => expect(mockList).toHaveBeenCalledTimes(2));
    expect(mockList).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 }));
  });
});
