import { type ReactNode } from 'react';
import { act, renderHook } from '@testing-library/react';
import { createMemoryRouter, RouterProvider, useLocation } from 'react-router';
import { useOrderParams } from '~/hooks/useOrderParams';

type UseOrderParamsOptions = { resetPageOnChange?: boolean };

let currentSearch = '';

function SearchReader() {
  currentSearch = new URLSearchParams(useLocation().search).toString();
  return null;
}

function renderOrderParams(initialPath = '/', options: UseOrderParamsOptions = {}) {
  function Wrapper({ children }: { children: ReactNode }) {
    const router = createMemoryRouter(
      [
        {
          path: '*',
          element: (
            <>
              <SearchReader />
              {children}
            </>
          ),
        },
      ],
      { initialEntries: [initialPath] },
    );
    return <RouterProvider router={router} />;
  }
  return renderHook(() => useOrderParams(options), { wrapper: Wrapper });
}

describe('useOrderParams', () => {
  it('reads orderBy and orderDirection from the URL', () => {
    const { result } = renderOrderParams('/?order_by=name&order_direction=desc');
    expect(result.current.sort).toEqual({ orderBy: 'name', orderDirection: 'desc' });
  });

  it('defaults orderDirection to asc when only order_by is present', () => {
    const { result } = renderOrderParams('/?order_by=name');
    expect(result.current.sort).toEqual({ orderBy: 'name', orderDirection: 'asc' });
  });

  it('returns an empty sort when no order_by is present', () => {
    const { result } = renderOrderParams('/?order_direction=desc');
    expect(result.current.sort).toEqual({});
  });

  it('toggleSort on a new column writes order_by with asc', () => {
    const { result } = renderOrderParams('/');
    act(() => result.current.toggleSort('name'));
    expect(currentSearch).toBe('order_by=name&order_direction=asc');
  });

  it('toggleSort on the active asc column cycles to desc', () => {
    const { result } = renderOrderParams('/?order_by=name&order_direction=asc');
    act(() => result.current.toggleSort('name'));
    expect(currentSearch).toBe('order_by=name&order_direction=desc');
  });

  it('toggleSort on the active desc column clears the sort', () => {
    const { result } = renderOrderParams('/?order_by=name&order_direction=desc');
    act(() => result.current.toggleSort('name'));
    expect(currentSearch).toBe('');
  });

  it('resets page to 1 by removing it when the sort changes', () => {
    const { result } = renderOrderParams('/?page=3');
    act(() => result.current.toggleSort('name'));
    expect(currentSearch).toBe('order_by=name&order_direction=asc');
  });

  it('keeps the page param when resetPageOnChange is false', () => {
    const { result } = renderOrderParams('/?page=3', { resetPageOnChange: false });
    act(() => result.current.toggleSort('name'));
    expect(currentSearch).toBe('page=3&order_by=name&order_direction=asc');
  });

  it('setSort with an empty sort removes both order params', () => {
    const { result } = renderOrderParams('/?order_by=name&order_direction=desc');
    act(() => result.current.setSort({}));
    expect(currentSearch).toBe('');
  });
});
