import { screen, waitFor } from '@testing-library/react';
import { useOutletContext } from 'react-router';
import ItemLayout, { loader } from '~/routes/items/item-layout';
import type { ItemOutletContext } from '~/routes/items/item-layout';
import { ApiError, itemsApi } from '~/data/api';
import { mockItem } from '../mocks';
import { createRouteStub } from '../utils/createStub';

jest.mock('~/data/api', () => ({
  ApiError: jest.requireActual('~/data/api').ApiError,
  itemsApi: { get: jest.fn() },
}));

const mockGet = jest.mocked(itemsApi.get);

function Child() {
  const { item } = useOutletContext<ItemOutletContext>();
  return <p>Loaded {item.name}</p>;
}

describe('item-layout route', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches the item by the route param', async () => {
    mockGet.mockResolvedValue(mockItem);
    createRouteStub(
      [
        {
          path: '/items/:itemId',
          loader,
          Component: ItemLayout,
          children: [{ index: true, Component: Child }],
        },
      ],
      { initialPath: '/items/1' },
    );

    await waitFor(() => expect(mockGet).toHaveBeenCalledWith(1));
  });

  it('shares the loaded item with its children via outlet context', async () => {
    mockGet.mockResolvedValue(mockItem);
    createRouteStub(
      [
        {
          path: '/items/:itemId',
          loader,
          Component: ItemLayout,
          children: [{ index: true, Component: Child }],
        },
      ],
      { initialPath: '/items/1' },
    );

    expect(await screen.findByText('Loaded First item')).toBeInTheDocument();
  });

  it('lets an api error from the loader bubble to the error boundary', async () => {
    mockGet.mockRejectedValue(new ApiError(404, 'Item not found.'));

    const args = {
      params: { itemId: '99' },
      request: new Request('http://localhost/items/99'),
      context: {},
    } as Parameters<typeof loader>[0];
    await expect(loader(args)).rejects.toThrow('Item not found.');
  });
});
