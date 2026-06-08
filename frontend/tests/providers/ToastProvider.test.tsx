import { render, screen, fireEvent, act, renderHook } from '@testing-library/react';
import { ToastProvider, useToast } from '~/providers/ToastProvider';

function ToastHarness() {
  const { showSuccess, showError, showInfo, showToast } = useToast();
  return (
    <div>
      <button onClick={() => showSuccess('Saved')}>show-success</button>
      <button onClick={() => showError('Failed')}>show-error</button>
      <button onClick={() => showInfo('Heads up')}>show-info</button>
      <button onClick={() => showToast('Sticky', 'info', 0)}>show-sticky</button>
    </div>
  );
}

function renderToasts(): void {
  render(
    <ToastProvider>
      <ToastHarness />
    </ToastProvider>,
  );
}

describe('ToastProvider', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('shows a success toast', () => {
    renderToasts();
    fireEvent.click(screen.getByRole('button', { name: 'show-success' }));
    expect(screen.getByText('Saved')).toBeInTheDocument();
  });

  it('auto-dismisses a toast after its duration elapses', () => {
    renderToasts();
    fireEvent.click(screen.getByRole('button', { name: 'show-info' }));
    act(() => {
      jest.advanceTimersByTime(3000);
    });
    expect(screen.queryByText('Heads up')).not.toBeInTheDocument();
  });

  it('shows an error toast', () => {
    renderToasts();
    fireEvent.click(screen.getByRole('button', { name: 'show-error' }));
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('does not auto-dismiss a toast with duration 0', () => {
    renderToasts();
    fireEvent.click(screen.getByRole('button', { name: 'show-sticky' }));
    act(() => {
      jest.advanceTimersByTime(10000);
    });
    expect(screen.getByText('Sticky')).toBeInTheDocument();
  });

  it('removes a toast when its close button is clicked', () => {
    renderToasts();
    fireEvent.click(screen.getByRole('button', { name: 'show-sticky' }));
    fireEvent.click(screen.getByRole('button', { name: 'Close notification' }));
    expect(screen.queryByText('Sticky')).not.toBeInTheDocument();
  });

  it('throws when useToast is used outside a ToastProvider', () => {
    expect(() => renderHook(() => useToast())).toThrow(
      'useToast must be used within a ToastProvider',
    );
  });
});
