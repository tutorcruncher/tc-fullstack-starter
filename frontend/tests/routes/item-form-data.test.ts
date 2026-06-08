import { parseItemForm } from '~/routes/items/item-form-data';

function formData(fields: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(fields)) {
    data.set(key, value);
  }
  return data;
}

describe('parseItemForm', () => {
  it('returns a typed payload for valid input', () => {
    const result = parseItemForm(
      formData({
        name: 'My item',
        description: 'Some details',
        status: 'active',
        category: 'sales',
      }),
    );
    expect(result).toEqual({
      payload: {
        name: 'My item',
        description: 'Some details',
        status: 'active',
        category: 'sales',
      },
    });
  });

  it('trims surrounding whitespace from text fields', () => {
    const result = parseItemForm(
      formData({
        name: '  My item  ',
        description: '  Some details  ',
        status: 'draft',
        category: '  sales  ',
      }),
    );
    expect(result).toEqual({
      payload: { name: 'My item', description: 'Some details', status: 'draft', category: 'sales' },
    });
  });

  it('coerces a blank category to null', () => {
    const result = parseItemForm(
      formData({ name: 'My item', description: '', status: 'active', category: '' }),
    );
    expect(result).toEqual({
      payload: { name: 'My item', description: '', status: 'active', category: null },
    });
  });

  it('returns a name error when the name is missing', () => {
    const result = parseItemForm(
      formData({ name: '', description: 'Some details', status: 'active' }),
    );
    expect(result).toEqual({ errors: { name: 'Name is required.' } });
  });

  it('returns a status error when the status is invalid', () => {
    const result = parseItemForm(
      formData({ name: 'My item', description: 'Some details', status: 'bogus' }),
    );
    expect(result).toEqual({ errors: { status: 'Choose a status.' } });
  });

  it('returns a status error when the status is missing', () => {
    const result = parseItemForm(formData({ name: 'My item', description: 'Some details' }));
    expect(result).toEqual({ errors: { status: 'Choose a status.' } });
  });

  it('returns both field errors when name and status are both invalid', () => {
    const result = parseItemForm(
      formData({ name: '', description: 'Some details', status: 'bogus' }),
    );
    expect(result).toEqual({ errors: { name: 'Name is required.', status: 'Choose a status.' } });
  });
});
