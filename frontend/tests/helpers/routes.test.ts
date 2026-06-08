import { isPublicRoute, PUBLIC_ROUTE_PREFIXES, PUBLIC_ROUTES } from '~/helpers/routes';

const mutablePrefixes = PUBLIC_ROUTE_PREFIXES as string[];

describe('isPublicRoute', () => {
  afterEach(() => {
    mutablePrefixes.length = 0;
  });

  it('returns true for an exact public route', () => {
    expect(isPublicRoute('/login')).toBe(true);
  });

  it('returns false for a route not in the public list', () => {
    expect(isPublicRoute('/items')).toBe(false);
  });

  it('returns false for a path that only prefixes a public route', () => {
    expect(isPublicRoute('/log')).toBe(false);
  });

  it('matches a configured prefix and anything nested beneath it', () => {
    mutablePrefixes.push('/public');
    expect(isPublicRoute('/public/docs')).toBe(true);
  });

  it('returns false when no configured prefix matches the path', () => {
    mutablePrefixes.push('/public');
    expect(isPublicRoute('/items')).toBe(false);
  });
});

describe('route config constants', () => {
  it('exposes login as the only exact public route', () => {
    expect(PUBLIC_ROUTES).toEqual(['/login']);
  });

  it('ships with no public prefixes by default', () => {
    expect(PUBLIC_ROUTE_PREFIXES).toEqual([]);
  });
});
