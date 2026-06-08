import { ApiError, apiRequest, itemsApi, apiBaseUrl } from '~/data/api';
import { safeGetItem } from '~/helpers/storage';
import { mockItem, mockItems } from '../mocks';

jest.mock('~/helpers/storage');

const mockGetItem = jest.mocked(safeGetItem);
const mockFetch = jest.fn();

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
}

function lastCall(): [string, RequestInit] {
  return mockFetch.mock.calls.at(-1) as [string, RequestInit];
}

describe('apiRequest', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = mockFetch as typeof fetch;
    mockGetItem.mockReturnValue(null);
  });

  it('prefixes the path with the base url', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));
    await apiRequest('/items');
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/items`);
  });

  it('sends a JSON content-type header', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));
    await apiRequest('/items');
    expect((lastCall()[1].headers as Record<string, string>)['Content-Type']).toBe(
      'application/json',
    );
  });

  it('attaches a bearer token from storage when present', async () => {
    mockGetItem.mockReturnValue('abc123');
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));
    await apiRequest('/items');
    expect((lastCall()[1].headers as Record<string, string>).Authorization).toBe('Bearer abc123');
  });

  it('omits the Authorization header when there is no token', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));
    await apiRequest('/items');
    expect((lastCall()[1].headers as Record<string, string>).Authorization).toBeUndefined();
  });

  it('parses and returns the JSON body on a successful response', async () => {
    mockFetch.mockResolvedValue(jsonResponse(mockItem));
    await expect(apiRequest('/items/1')).resolves.toEqual(mockItem);
  });

  it('throws an ApiError carrying the response status on a non-ok response', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ detail: 'Not found' }, { status: 404 }));
    await expect(apiRequest('/items/1')).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
    });
  });

  it('uses json.detail as the error message when present', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ detail: 'Boom detail' }, { status: 500 }));
    await expect(apiRequest('/items')).rejects.toThrow('Boom detail');
  });

  it('falls back to json.error when detail is absent', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ error: 'Boom error' }, { status: 400 }));
    await expect(apiRequest('/items')).rejects.toThrow('Boom error');
  });

  it('falls back to the status text when the error body has neither detail nor error', async () => {
    mockFetch.mockResolvedValue(
      new Response('not json', { status: 503, statusText: 'Service Unavailable' }),
    );
    await expect(apiRequest('/items')).rejects.toThrow('Service Unavailable');
  });
});

describe('itemsApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = mockFetch as typeof fetch;
    mockGetItem.mockReturnValue(null);
  });

  it('list requests GET /items with the filters as a query string', async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ items: mockItems, total: 3, page: 1, page_size: 20 }),
    );
    await itemsApi.list({ page: 2, search: 'widget' });
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/items?page=2&search=widget`);
    expect(lastCall()[1].method).toBeUndefined();
  });

  it('list omits empty filter values from the query string', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ items: [], total: 0, page: 1, page_size: 20 }));
    await itemsApi.list({ page: 1, search: '' });
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/items?page=1`);
  });

  it('list requests GET /items with no query string when no filters are given', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ items: [], total: 0, page: 1, page_size: 20 }));
    await itemsApi.list();
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/items`);
  });

  it('get requests GET /items/:id', async () => {
    mockFetch.mockResolvedValue(jsonResponse(mockItem));
    await itemsApi.get(5);
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/items/5`);
    expect(lastCall()[1].method).toBeUndefined();
  });

  it('create POSTs the payload as JSON to /items', async () => {
    mockFetch.mockResolvedValue(jsonResponse(mockItem));
    await itemsApi.create({ name: 'New', description: 'D', status: 'draft', category: null });
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/items`);
    expect(lastCall()[1].method).toBe('POST');
    expect(lastCall()[1].body).toBe(
      JSON.stringify({ name: 'New', description: 'D', status: 'draft', category: null }),
    );
  });

  it('update PUTs the payload as JSON to /items/:id', async () => {
    mockFetch.mockResolvedValue(jsonResponse(mockItem));
    await itemsApi.update(7, { name: 'Edit', description: 'D', status: 'active', category: null });
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/items/7`);
    expect(lastCall()[1].method).toBe('PUT');
    expect(lastCall()[1].body).toBe(
      JSON.stringify({ name: 'Edit', description: 'D', status: 'active', category: null }),
    );
  });

  it('remove DELETEs /items/:id', async () => {
    mockFetch.mockResolvedValue(jsonResponse(null));
    await itemsApi.remove(9);
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/items/9`);
    expect(lastCall()[1].method).toBe('DELETE');
  });
});

describe('ApiError', () => {
  it('exposes the status and message it was constructed with', () => {
    const error = new ApiError(418, "I'm a teapot");
    expect(error).toBeInstanceOf(Error);
    expect(error.status).toBe(418);
    expect(error.message).toBe("I'm a teapot");
    expect(error.name).toBe('ApiError');
  });
});
