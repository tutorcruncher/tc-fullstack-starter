import { PAGE_SIZE } from '~/helpers/pagination';

describe('PAGE_SIZE', () => {
  it('exposes the default page size', () => {
    expect(PAGE_SIZE.default).toBe(20);
  });

  it('exposes the large page size', () => {
    expect(PAGE_SIZE.large).toBe(50);
  });

  it('exposes only the documented page-size keys', () => {
    expect(PAGE_SIZE).toEqual({ default: 20, large: 50 });
  });
});
