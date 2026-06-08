import { safeGetItem, safeRemoveItem, safeSetItem } from '~/helpers/storage';

describe('safeGetItem', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  it('returns the stored value', () => {
    localStorage.setItem('theme', 'dark');
    expect(safeGetItem('theme')).toBe('dark');
  });

  it('returns null for a missing key', () => {
    expect(safeGetItem('missing')).toBeNull();
  });

  it('returns null and warns when localStorage throws', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    expect(safeGetItem('theme')).toBeNull();
    expect(warn).toHaveBeenCalledWith(
      'Failed to read localStorage key "theme":',
      expect.any(Error),
    );
  });
});

describe('safeSetItem', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  it('writes the value and returns true', () => {
    expect(safeSetItem('theme', 'dark')).toBe(true);
    expect(localStorage.getItem('theme')).toBe('dark');
  });

  it('returns false and warns when localStorage throws', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('quota exceeded');
    });
    expect(safeSetItem('theme', 'dark')).toBe(false);
    expect(warn).toHaveBeenCalledWith(
      'Failed to write localStorage key "theme":',
      expect.any(Error),
    );
  });
});

describe('safeRemoveItem', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.restoreAllMocks();
  });

  it('removes the stored value', () => {
    localStorage.setItem('theme', 'dark');
    safeRemoveItem('theme');
    expect(localStorage.getItem('theme')).toBeNull();
  });

  it('warns when localStorage throws', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    jest.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    safeRemoveItem('theme');
    expect(warn).toHaveBeenCalledWith(
      'Failed to remove localStorage key "theme":',
      expect.any(Error),
    );
  });
});
