import { act, renderHook, waitFor } from '@testing-library/react';
import { useAsyncAction } from '~/hooks/useAsyncAction';

describe('useAsyncAction', () => {
  it('starts idle with no loading and no error', () => {
    const { result } = renderHook(() => useAsyncAction(jest.fn().mockResolvedValue('ok')));
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sets isLoading true while the action runs and false after it resolves', async () => {
    let resolve!: (value: string) => void;
    const action = jest.fn(() => new Promise<string>((r) => (resolve = r)));
    const { result } = renderHook(() => useAsyncAction(action));

    let executed!: Promise<string | undefined>;
    act(() => {
      executed = result.current.execute();
    });
    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolve('done');
      await executed;
    });
    expect(result.current.isLoading).toBe(false);
  });

  it('returns the action result on success', async () => {
    const action = jest.fn<Promise<string>, []>().mockResolvedValue('value');
    const { result } = renderHook(() => useAsyncAction(action));

    let returned: string | undefined;
    await act(async () => {
      returned = await result.current.execute();
    });
    expect(returned).toBe('value');
  });

  it('captures the thrown error message and returns undefined on failure', async () => {
    const { result } = renderHook(() =>
      useAsyncAction(jest.fn().mockRejectedValue(new Error('Boom'))),
    );

    let returned: unknown;
    await act(async () => {
      returned = await result.current.execute();
    });
    expect(returned).toBeUndefined();
    expect(result.current.error).toBe('Boom');
  });

  it('falls back to a generic message when the rejection is not an Error', async () => {
    const { result } = renderHook(() => useAsyncAction(jest.fn().mockRejectedValue('nope')));

    await act(async () => {
      await result.current.execute();
    });
    expect(result.current.error).toBe('Something went wrong');
  });

  it('clears a previous error when a new execution starts', async () => {
    const action = jest.fn().mockRejectedValueOnce(new Error('First')).mockResolvedValueOnce('ok');
    const { result } = renderHook(() => useAsyncAction(action));

    await act(async () => {
      await result.current.execute();
    });
    expect(result.current.error).toBe('First');

    await act(async () => {
      await result.current.execute();
    });
    expect(result.current.error).toBeNull();
  });

  it('reset clears loading and error', async () => {
    const { result } = renderHook(() =>
      useAsyncAction(jest.fn().mockRejectedValue(new Error('Boom'))),
    );

    await act(async () => {
      await result.current.execute();
    });
    expect(result.current.error).toBe('Boom');

    act(() => {
      result.current.reset();
    });
    await waitFor(() => expect(result.current.error).toBeNull());
    expect(result.current.isLoading).toBe(false);
  });
});
