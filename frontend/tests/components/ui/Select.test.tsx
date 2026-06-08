import { screen } from '@testing-library/react';
import selectEvent from 'react-select-event';
import { Select } from '~/components/ui';
import { renderWithRouter } from '../../utils/render';

interface StatusOption {
  value: string;
  label: string;
}

const options: StatusOption[] = [
  { value: 'draft', label: 'Draft' },
  { value: 'active', label: 'Active' },
  { value: 'archived', label: 'Archived' },
];

describe('Select', () => {
  it('renders a label wired to the control', () => {
    renderWithRouter(<Select label="Status" options={options} />);
    expect(screen.getByLabelText('Status')).toBeInTheDocument();
  });

  it('marks the label as required', () => {
    renderWithRouter(<Select label="Status" options={options} required />);
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('renders the error message below the control', () => {
    renderWithRouter(<Select label="Status" options={options} error="Status is required" />);
    expect(screen.getByText('Status is required')).toBeInTheDocument();
  });

  it('selects an option through the react-select dropdown', async () => {
    const onChange = jest.fn();
    renderWithRouter(<Select label="Status" options={options} onChange={onChange} />);
    await selectEvent.select(screen.getByLabelText('Status'), 'Active');
    expect(onChange).toHaveBeenCalledWith(
      { value: 'active', label: 'Active' },
      expect.objectContaining({ action: 'select-option' }),
    );
  });
});
