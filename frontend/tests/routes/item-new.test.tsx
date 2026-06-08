import { action } from '~/routes/items/item-new';
import { ApiError, itemsApi } from '~/data/api';
import { mockItem } from '../mocks';

jest.mock('~/data/api', () => ({
  ApiError: jest.requireActual('~/data/api').ApiError,
  itemsApi: { create: jest.fn() },
}));

const mockCreate = jest.mocked(itemsApi.create);

function runAction(fields: Record<string, string>) {
  const request = new Request('http://localhost/items/new', {
    method: 'POST',
    body: new URLSearchParams(fields),
  });
  return action({ request, params: {}, context: {} } as Parameters<typeof action>[0]);
}

describe('item-new route action', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('creates the item and redirects to its detail page on success', async () => {
    mockCreate.mockResolvedValue({ ...mockItem, id: 7 });

    const result = await runAction({
      name: 'My item',
      description: 'Some details',
      status: 'draft',
    });

    expect(mockCreate).toHaveBeenCalledWith({
      name: 'My item',
      description: 'Some details',
      status: 'draft',
      category: null,
    });
    expect(result).toBeInstanceOf(Response);
    expect((result as Response).status).toBe(302);
    expect((result as Response).headers.get('Location')).toBe('/items/7');
  });

  it('returns a field error and does not call the api when the name is blank', async () => {
    const result = await runAction({ name: '', description: 'Some details', status: 'draft' });

    expect(mockCreate).not.toHaveBeenCalled();
    expect(result).toEqual({ errors: { name: 'Name is required.' } });
  });

  it('returns the api error message as a form error when create rejects', async () => {
    mockCreate.mockRejectedValue(new ApiError(400, 'Name already taken.'));

    const result = await runAction({
      name: 'My item',
      description: 'Some details',
      status: 'draft',
    });

    expect(result).toEqual({ errors: { form: 'Name already taken.' } });
  });

  it('rethrows a non-api error so it bubbles to the ErrorBoundary', async () => {
    mockCreate.mockRejectedValue(new Error('network down'));

    await expect(
      runAction({ name: 'My item', description: 'Some details', status: 'draft' }),
    ).rejects.toThrow('network down');
  });
});
