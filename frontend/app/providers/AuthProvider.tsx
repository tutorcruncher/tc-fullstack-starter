/**
 * Client-side auth context. Reads the bearer token from storage, validates it
 * by fetching the current user via `authApi.checkUser`, and exposes the result
 * through `useAuth`. When validation fails (or no token is present) on a
 * non-public route, it redirects to `/login` preserving the attempted URL.
 *
 * SSR caveat: this validates the user on the client (localStorage has no
 * server equivalent). For authenticated SSR route loaders, forward the
 * cookie / Authorization header from the incoming request instead.
 */
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router';
import { authApi } from '~/data/api';
import { isPublicRoute } from '~/helpers/routes';
import { safeGetItem } from '~/helpers/storage';
import type { User } from '~/types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = 'token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    let cancelled = false;

    const redirectToLogin = (): void => {
      if (!isPublicRoute(location.pathname)) {
        const target = location.pathname + location.search;
        navigate(`/login?redirect_url=${encodeURIComponent(target)}`, { replace: true });
      }
    };

    const checkAuth = async (): Promise<void> => {
      if (!safeGetItem(TOKEN_KEY)) {
        if (cancelled) {
          return;
        }
        setUser(null);
        setLoading(false);
        redirectToLogin();
        return;
      }
      try {
        const currentUser = await authApi.checkUser();
        if (cancelled) {
          return;
        }
        setUser(currentUser);
      } catch (error) {
        console.error(error);
        if (cancelled) {
          return;
        }
        setUser(null);
        redirectToLogin();
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void checkAuth();

    return () => {
      cancelled = true;
    };
  }, [location.pathname, location.search, navigate]);

  const value = useMemo<AuthContextValue>(() => ({ user, loading }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
