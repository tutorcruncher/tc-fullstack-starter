import { screen, fireEvent } from '@testing-library/react';
import { Pagination } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

describe('Pagination', () => {
  it('renders nothing when there is a single page', () => {
    const { container } = renderWithRouter(
      <Pagination total={5} page={1} pageSize={20} totalPages={1} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders a button for every page when the range fits without gaps', () => {
    renderWithRouter(<Pagination total={60} page={1} pageSize={20} totalPages={3} />);
    expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '2' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '3' })).toBeInTheDocument();
  });

  it('collapses distant pages into ellipsis gaps', () => {
    renderWithRouter(<Pagination total={200} page={5} pageSize={20} totalPages={10} />);
    expect(screen.getAllByText('…')).toHaveLength(2);
    expect(screen.queryByRole('button', { name: '8' })).not.toBeInTheDocument();
  });

  it('marks the current page with aria-current', () => {
    renderWithRouter(<Pagination total={60} page={2} pageSize={20} totalPages={3} />);
    expect(screen.getByRole('button', { name: '2' })).toHaveAttribute('aria-current', 'page');
  });

  it('calls onChange with the chosen page number', () => {
    const onChange = jest.fn();
    renderWithRouter(
      <Pagination total={60} page={1} pageSize={20} totalPages={3} onChange={onChange} />,
    );
    fireEvent.click(screen.getByRole('button', { name: '3' }));
    expect(onChange).toHaveBeenCalledWith(3);
  });

  it('calls onChange with the previous page when Previous is clicked', () => {
    const onChange = jest.fn();
    renderWithRouter(
      <Pagination total={60} page={2} pageSize={20} totalPages={3} onChange={onChange} />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Previous page' }));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it('disables the Previous button on the first page', () => {
    renderWithRouter(<Pagination total={60} page={1} pageSize={20} totalPages={3} />);
    expect(screen.getByRole('button', { name: 'Previous page' })).toBeDisabled();
  });

  it('disables the Next button on the last page', () => {
    renderWithRouter(<Pagination total={60} page={3} pageSize={20} totalPages={3} />);
    expect(screen.getByRole('button', { name: 'Next page' })).toBeDisabled();
  });

  it('summarises the visible range and total', () => {
    renderWithRouter(<Pagination total={55} page={2} pageSize={20} totalPages={3} />);
    expect(screen.getByText(/Showing/)).toHaveTextContent('Showing 21–40 of 55');
  });

  it('caps the visible range at the total on the final page', () => {
    renderWithRouter(<Pagination total={55} page={3} pageSize={20} totalPages={3} />);
    expect(screen.getByText(/Showing/)).toHaveTextContent('Showing 41–55 of 55');
  });
});
