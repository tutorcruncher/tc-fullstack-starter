import { screen, fireEvent } from '@testing-library/react';
import { SearchInput } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('SearchInput', () => {
  it('uses the placeholder as the accessible label', () => {
    renderWithRouter(
      <SearchInput value="" onChange={() => {}} onSubmit={() => {}} placeholder="Find items" />,
    );
    expect(screen.getByRole('searchbox', { name: 'Find items' })).toBeInTheDocument();
  });

  it('reflects the controlled value', () => {
    renderWithRouter(<SearchInput value="apples" onChange={() => {}} onSubmit={() => {}} />);
    expect(screen.getByRole('searchbox')).toHaveValue('apples');
  });

  it('calls onChange with the new value as the user types', () => {
    const onChange = jest.fn();
    renderWithRouter(<SearchInput value="" onChange={onChange} onSubmit={() => {}} />);
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'pears' } });
    expect(onChange).toHaveBeenCalledWith('pears');
  });

  it('calls onSubmit when the form is submitted', () => {
    const onSubmit = jest.fn((event) => event.preventDefault());
    renderWithRouter(<SearchInput value="q" onChange={() => {}} onSubmit={onSubmit} />);
    fireEvent.submit(screen.getByRole('search'));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('shows the search icon when not loading', () => {
    const { container } = renderWithRouter(
      <SearchInput value="" onChange={() => {}} onSubmit={() => {}} />,
    );
    expect(container.querySelector('.lucide-search')).toBeInTheDocument();
    expect(container.querySelector('.animate-spin')).not.toBeInTheDocument();
  });

  it('swaps the icon for a spinner while loading', () => {
    const { container } = renderWithRouter(
      <SearchInput value="" onChange={() => {}} onSubmit={() => {}} loading />,
    );
    expect(container.querySelector('.animate-spin')).toBeInTheDocument();
    expect(container.querySelector('.lucide-search')).not.toBeInTheDocument();
  });

  it('marks the input busy while loading', () => {
    renderWithRouter(<SearchInput value="" onChange={() => {}} onSubmit={() => {}} loading />);
    expect(screen.getByRole('searchbox')).toHaveAttribute('aria-busy', 'true');
  });
});
