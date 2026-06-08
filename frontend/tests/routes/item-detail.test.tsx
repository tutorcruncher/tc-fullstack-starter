import { screen, waitFor } from '@testing-library/react';
import ItemDetail, { action } from '~/routes/items/item-detail';
import ItemLayout, { loader as layoutLoader } from '~/routes/items/item-layout';
import { ApiError, itemsApi } from '~/data/api';
import { mockItem } from '../mocks';
import { createRouteStub } from '../utils/createStub';

jest.mock('~/data/api', () => ({
  ApiError: jest.requireActual('~/data/api').ApiError,
  itemsApi: { get: jest.fn(), remove: jest.fn() },
}));

const mockGet = jest.mocked(itemsApi.get);
const mockRemove = jest.mocked(itemsApi.remove);

function runAction(itemId: string) {
  return action({
    request: new Request(`http://localhost/items/${itemId}`, { method: 'POST' }),
    params: { itemId },
    context: {},
  } as Parameters<typeof action>[0]);
}

function renderDetail(item = mockItem): void {
  mockGet.mockResolvedValue(item);
  createRouteStub(
    [
      {
        path: '/items/:itemId',
        loader: layoutLoader,
        Component: ItemLayout,
        children: [{ index: true, Component: ItemDetail }],
      },
    ],
    { initialPath: `/items/${item.id}` },
  );
}

describe('item-detail route', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the item name loaded by the layout loader', async () => {
    renderDetail();
    expect(
      await screen.findByRole('heading', { name: 'First item', level: 1 }),
    ).toBeInTheDocument();
  });

  it('renders the status label for the item', async () => {
    renderDetail();
    await waitFor(() => expect(screen.getByText('Active')).toBeInTheDocument());
  });

  it('renders the category value for the item', async () => {
    renderDetail();
    await waitFor(() => expect(screen.getByText('general')).toBeInTheDocument());
  });

  it('renders a dash when the item has no category', async () => {
    renderDetail({ ...mockItem, category: null });
    await waitFor(() => expect(screen.getByText('—')).toBeInTheDocument());
  });

  it('links to the edit page for the item', async () => {
    renderDetail();
    await waitFor(() =>
      expect(screen.getByRole('link', { name: /edit/i })).toHaveAttribute('href', '/items/1/edit'),
    );
  });

  it('removes the item and redirects to the list on the delete action', async () => {
    mockRemove.mockResolvedValue(undefined);

    const result = await runAction('3');

    expect(mockRemove).toHaveBeenCalledWith(3);
    expect(result).toBeInstanceOf(Response);
    expect((result as Response).status).toBe(302);
    expect((result as Response).headers.get('Location')).toBe('/items');
  });

  it('lets an api error from remove bubble out of the action', async () => {
    mockRemove.mockRejectedValue(new ApiError(404, 'Item not found.'));

    await expect(runAction('3')).rejects.toThrow('Item not found.');
  });
});
