import { render, screen, waitFor, renderHook } from '@testing-library/react';
import { createRoutesStub, useLocation } from 'react-router';
import { AuthProvider, useAuth } from '~/providers/AuthProvider';
import { authApi } from '~/data/api';
import { safeGetItem } from '~/helpers/storage';
import { mockUser } from '../mocks';

jest.mock('~/data/api', () => ({
  authApi: { checkUser: jest.fn() },
}));
jest.mock('~/helpers/storage');

const mockCheckUser = jest.mocked(authApi.checkUser);
const mockGetItem = jest.mocked(safeGetItem);

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname + location.search}</div>;
}

function AuthProbe() {
  const { user, loading } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="user">{user ? user.name : 'none'}</span>
    </div>
  );
}

function renderAuth(initialPath: string): void {
  const Stub = createRoutesStub([
    {
      path: '*',
      Component: () => (
        <AuthProvider>
          <LocationProbe />
          <AuthProbe />
        </AuthProvider>
      ),
    },
  ]);
  render(<Stub initialEntries={[initialPath]} />);
}

describe('AuthProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  it('sets the user returned by authApi.checkUser when a token is present', async () => {
    mockGetItem.mockReturnValue('a-token');
    mockCheckUser.mockResolvedValue(mockUser);
    renderAuth('/items');

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Ada Lovelace'));
    expect(screen.getByTestId('loading')).toHaveTextContent('false');
  });

  it('validates the token by calling authApi.checkUser exactly once', async () => {
    mockGetItem.mockReturnValue('a-token');
    mockCheckUser.mockResolvedValue(mockUser);
    renderAuth('/items');

    await waitFor(() => expect(mockCheckUser).toHaveBeenCalledTimes(1));
  });

  it('does not call authApi.checkUser when no token is stored', async () => {
    mockGetItem.mockReturnValue(null);
    renderAuth('/items');

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'));
    expect(mockCheckUser).not.toHaveBeenCalled();
  });

  it('redirects to login preserving the attempted url when no token is stored', async () => {
    mockGetItem.mockReturnValue(null);
    renderAuth('/items?page=2');

    await waitFor(() =>
      expect(screen.getByTestId('location')).toHaveTextContent(
        '/login?redirect_url=%2Fitems%3Fpage%3D2',
      ),
    );
  });

  it('redirects to login when token validation rejects on a protected route', async () => {
    mockGetItem.mockReturnValue('bad-token');
    mockCheckUser.mockRejectedValue(new Error('invalid'));
    renderAuth('/items');

    await waitFor(() =>
      expect(screen.getByTestId('location')).toHaveTextContent('/login?redirect_url=%2Fitems'),
    );
    expect(screen.getByTestId('user')).toHaveTextContent('none');
  });

  it('does not redirect when the unauthenticated route is public', async () => {
    mockGetItem.mockReturnValue(null);
    renderAuth('/login');

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'));
    expect(screen.getByTestId('location')).toHaveTextContent('/login');
  });

  it('throws when useAuth is used outside an AuthProvider', () => {
    expect(() => renderHook(() => useAuth())).toThrow(
      'useAuth must be used within an AuthProvider',
    );
  });
});
