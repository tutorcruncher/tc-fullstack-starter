import { screen, fireEvent } from '@testing-library/react';
import { Input, Textarea } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('Input', () => {
  it('associates the visible label with the input', () => {
    renderWithRouter(<Input label="Email" value="" onChange={() => {}} />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('reflects the controlled value', () => {
    renderWithRouter(<Input label="Email" value="a@b.com" onChange={() => {}} />);
    expect(screen.getByLabelText('Email')).toHaveValue('a@b.com');
  });

  it('calls onChange when the user types', () => {
    const onChange = jest.fn();
    renderWithRouter(<Input label="Email" value="" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'x' } });
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it('renders the error text', () => {
    renderWithRouter(<Input label="Email" value="" onChange={() => {}} error="Required" />);
    expect(screen.getByText('Required')).toBeInTheDocument();
  });

  it('marks the field invalid and describes it with the error when there is an error', () => {
    renderWithRouter(<Input label="Email" value="" onChange={() => {}} error="Required" />);
    const input = screen.getByLabelText('Email');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    const describedById = input.getAttribute('aria-describedby');
    expect(screen.getByText('Required')).toHaveAttribute('id', describedById);
  });

  it('does not mark the field invalid when there is no error', () => {
    renderWithRouter(<Input label="Email" value="" onChange={() => {}} />);
    const input = screen.getByLabelText('Email');
    expect(input).not.toHaveAttribute('aria-invalid');
    expect(input).not.toHaveAttribute('aria-describedby');
  });
});

describe('Textarea', () => {
  it('associates the visible label with the textarea', () => {
    renderWithRouter(<Textarea label="Notes" value="" onChange={() => {}} />);
    expect(screen.getByLabelText('Notes')).toBeInTheDocument();
  });

  it('calls onChange when the user types', () => {
    const onChange = jest.fn();
    renderWithRouter(<Textarea label="Notes" value="" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('Notes'), { target: { value: 'hello' } });
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it('marks the field invalid and describes it with the error when there is an error', () => {
    renderWithRouter(<Textarea label="Notes" value="" onChange={() => {}} error="Too short" />);
    const textarea = screen.getByLabelText('Notes');
    expect(textarea).toHaveAttribute('aria-invalid', 'true');
    const describedById = textarea.getAttribute('aria-describedby');
    expect(screen.getByText('Too short')).toHaveAttribute('id', describedById);
  });
});
