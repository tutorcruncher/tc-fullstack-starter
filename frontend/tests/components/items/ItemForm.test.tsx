import { screen, fireEvent } from '@testing-library/react';
import { ItemForm } from '~/components/items/ItemForm';
import { mockItem } from '../../mocks';
import { createRouteStub } from '../../utils/createStub';

function renderForm(): void {
  createRouteStub([
    {
      path: '/',
      Component: () => <ItemForm heading="New item" submitLabel="Create item" />,
    },
  ]);
}

describe('ItemForm', () => {
  it('renders the heading and submit label', () => {
    renderForm();
    expect(screen.getByRole('heading', { name: 'New item' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create item' })).toBeInTheDocument();
  });

  it('updates the name field as the user types', () => {
    renderForm();
    const nameInput = screen.getByLabelText(/name/i);
    fireEvent.change(nameInput, { target: { value: 'My item' } });
    expect(nameInput).toHaveValue('My item');
  });

  it('prefills the name and description fields from defaultValues when editing', () => {
    createRouteStub([
      {
        path: '/',
        Component: () => (
          <ItemForm heading="Edit item" submitLabel="Save changes" defaultValues={mockItem} />
        ),
      },
    ]);
    expect(screen.getByLabelText(/name/i)).toHaveValue(mockItem.name);
    expect(screen.getByLabelText(/description/i)).toHaveValue(mockItem.description);
  });

  it('shows the provided field error', () => {
    createRouteStub([
      {
        path: '/',
        Component: () => (
          <ItemForm
            heading="New item"
            submitLabel="Create item"
            errors={{ name: 'Name is required.' }}
          />
        ),
      },
    ]);
    const nameInput = screen.getByLabelText(/name/i);
    expect(screen.getByText('Name is required.')).toBeInTheDocument();
    expect(nameInput).toHaveAttribute('aria-invalid', 'true');
  });

  it('shows the top-level form error as an alert', () => {
    createRouteStub([
      {
        path: '/',
        Component: () => (
          <ItemForm
            heading="New item"
            submitLabel="Create item"
            errors={{ form: 'Something went wrong.' }}
          />
        ),
      },
    ]);
    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong.');
  });
});
