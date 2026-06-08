import { screen, waitFor } from '@testing-library/react';
import ItemEdit, { action } from '~/routes/items/item-edit';
import ItemLayout, { loader as layoutLoader } from '~/routes/items/item-layout';
import { ApiError, itemsApi } from '~/data/api';
import { mockItem } from '../mocks';
import { createRouteStub } from '../utils/createStub';

jest.mock('~/data/api', () => ({
  ApiError: jest.requireActual('~/data/api').ApiError,
  itemsApi: { get: jest.fn(), update: jest.fn() },
}));

const mockGet = jest.mocked(itemsApi.get);
const mockUpdate = jest.mocked(itemsApi.update);

function runAction(fields: Record<string, string>) {
  const request = new Request('http://localhost/items/3/edit', {
    method: 'POST',
    body: new URLSearchParams(fields),
  });
  return action({ request, params: { itemId: '3' }, context: {} } as Parameters<typeof action>[0]);
}

function renderEdit(): void {
  mockGet.mockResolvedValue(mockItem);
  createRouteStub(
    [
      {
        path: '/items/:itemId',
        loader: layoutLoader,
        Component: ItemLayout,
        children: [{ path: 'edit', Component: ItemEdit }],
      },
    ],
    { initialPath: '/items/1/edit' },
  );
}

describe('item-edit route', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('prefills the name from the item loaded by the layout loader', async () => {
    renderEdit();
    await waitFor(() => expect(screen.getByLabelText(/name/i)).toHaveValue('First item'));
  });

  it('prefills the description from the loaded item', async () => {
    renderEdit();
    await waitFor(() =>
      expect(screen.getByLabelText(/description/i)).toHaveValue(
        'A representative item used across tests.',
      ),
    );
  });

  it('renders an edit heading naming the item', async () => {
    renderEdit();
    expect(await screen.findByRole('heading', { name: 'Edit First item' })).toBeInTheDocument();
  });

  it('updates the item and redirects to its detail page on success', async () => {
    mockUpdate.mockResolvedValue(mockItem);

    const result = await runAction({
      name: 'Renamed',
      description: 'New details',
      status: 'active',
    });

    expect(mockUpdate).toHaveBeenCalledWith(3, {
      name: 'Renamed',
      description: 'New details',
      status: 'active',
      category: null,
    });
    expect(result).toBeInstanceOf(Response);
    expect((result as Response).status).toBe(302);
    expect((result as Response).headers.get('Location')).toBe('/items/3');
  });

  it('returns a field error and does not call the api when the name is blank', async () => {
    const result = await runAction({ name: '', description: 'New details', status: 'active' });

    expect(mockUpdate).not.toHaveBeenCalled();
    expect(result).toEqual({ errors: { name: 'Name is required.' } });
  });

  it('returns the api error message as a form error when update rejects', async () => {
    mockUpdate.mockRejectedValue(new ApiError(400, 'Name already taken.'));

    const result = await runAction({
      name: 'Renamed',
      description: 'New details',
      status: 'active',
    });

    expect(result).toEqual({ errors: { form: 'Name already taken.' } });
  });

  it('rethrows a non-api error so it bubbles to the ErrorBoundary', async () => {
    mockUpdate.mockRejectedValue(new Error('network down'));

    await expect(
      runAction({ name: 'Renamed', description: 'New details', status: 'active' }),
    ).rejects.toThrow('network down');
  });
});
