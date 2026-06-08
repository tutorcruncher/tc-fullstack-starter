import { screen, fireEvent } from '@testing-library/react';
import { Modal } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('Modal', () => {
  it('renders its content when open', () => {
    renderWithRouter(
      <Modal open onClose={jest.fn()} title="Edit item">
        <p>Body content</p>
      </Modal>,
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Body content')).toBeInTheDocument();
  });

  it('renders nothing when closed', () => {
    renderWithRouter(
      <Modal open={false} onClose={jest.fn()} title="Edit item">
        <p>Body content</p>
      </Modal>,
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.queryByText('Body content')).not.toBeInTheDocument();
  });

  it('calls onClose when Escape is pressed', () => {
    const onClose = jest.fn();
    renderWithRouter(
      <Modal open onClose={onClose} title="Edit item">
        <p>Body content</p>
      </Modal>,
    );
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when the backdrop is clicked', () => {
    const onClose = jest.fn();
    renderWithRouter(
      <Modal open onClose={onClose} title="Edit item">
        <p>Body content</p>
      </Modal>,
    );
    fireEvent.click(screen.getByRole('dialog').previousElementSibling!);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when the close button is clicked', () => {
    const onClose = jest.fn();
    renderWithRouter(
      <Modal open onClose={onClose} title="Edit item">
        <p>Body content</p>
      </Modal>,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('exposes the dialog as a modal labelled by its title and description', () => {
    renderWithRouter(
      <Modal open onClose={jest.fn()} title="Edit item" description="Update the details">
        <p>Body content</p>
      </Modal>,
    );
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAccessibleName('Edit item');
    expect(dialog).toHaveAccessibleDescription('Update the details');
  });

  it('moves focus to the dialog when opened', () => {
    renderWithRouter(
      <Modal open onClose={jest.fn()} title="Edit item">
        <button type="button">Inside</button>
      </Modal>,
    );
    expect(screen.getByRole('dialog')).toHaveFocus();
  });

  it('wraps focus from the last to the first focusable element on Tab', () => {
    renderWithRouter(
      <Modal open onClose={jest.fn()}>
        <button type="button">Inside</button>
      </Modal>,
    );
    const dialog = screen.getByRole('dialog');
    const first = screen.getByRole('button', { name: 'Close' });
    const last = screen.getByRole('button', { name: 'Inside' });
    last.focus();
    fireEvent.keyDown(dialog, { key: 'Tab' });
    expect(first).toHaveFocus();
  });

  it('wraps focus from the first to the last focusable element on Shift+Tab', () => {
    renderWithRouter(
      <Modal open onClose={jest.fn()}>
        <button type="button">Inside</button>
      </Modal>,
    );
    const dialog = screen.getByRole('dialog');
    const first = screen.getByRole('button', { name: 'Close' });
    const last = screen.getByRole('button', { name: 'Inside' });
    first.focus();
    fireEvent.keyDown(dialog, { key: 'Tab', shiftKey: true });
    expect(last).toHaveFocus();
  });
});
