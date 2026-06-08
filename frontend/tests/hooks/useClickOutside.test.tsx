import { createRef } from 'react';
import { fireEvent, render } from '@testing-library/react';
import { useClickOutside } from '~/hooks/useClickOutside';

interface HarnessProps {
  handler: () => void;
  isEnabled?: boolean;
}

function ClickOutsideHarness({ handler, isEnabled }: HarnessProps) {
  const ref = createRef<HTMLDivElement>();
  return <Inner forwardedRef={ref} handler={handler} isEnabled={isEnabled} />;
}

function Inner({
  forwardedRef,
  handler,
  isEnabled,
}: HarnessProps & { forwardedRef: React.RefObject<HTMLDivElement | null> }) {
  useClickOutside(forwardedRef, handler, isEnabled);
  return (
    <div>
      <div ref={forwardedRef} data-testid="inside">
        inside content
      </div>
      <div data-testid="outside">outside content</div>
    </div>
  );
}

describe('useClickOutside', () => {
  it('calls the handler on a mousedown outside the ref element', () => {
    const handler = jest.fn();
    const { getByTestId } = render(<ClickOutsideHarness handler={handler} />);
    fireEvent.mouseDown(getByTestId('outside'));
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('does not call the handler on a mousedown inside the ref element', () => {
    const handler = jest.fn();
    const { getByTestId } = render(<ClickOutsideHarness handler={handler} />);
    fireEvent.mouseDown(getByTestId('inside'));
    expect(handler).not.toHaveBeenCalled();
  });

  it('does nothing while disabled', () => {
    const handler = jest.fn();
    const { getByTestId } = render(<ClickOutsideHarness handler={handler} isEnabled={false} />);
    fireEvent.mouseDown(getByTestId('outside'));
    expect(handler).not.toHaveBeenCalled();
  });

  it('removes its document listener on unmount', () => {
    const handler = jest.fn();
    const { unmount } = render(<ClickOutsideHarness handler={handler} />);
    unmount();
    fireEvent.mouseDown(document.body);
    expect(handler).not.toHaveBeenCalled();
  });
});
