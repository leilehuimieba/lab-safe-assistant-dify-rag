import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const STORAGE_KEY = 'labsafe_password';

interface AuthContextValue {
  password: string;
  isLoggedIn: boolean;
  isChecking: boolean;
  login: (pw: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  password: '',
  isLoggedIn: false,
  isChecking: false,
  login: () => {},
  logout: () => {},
});

function restorePassword(): string {
  const sessionPassword = sessionStorage.getItem(STORAGE_KEY);
  if (sessionPassword) return sessionPassword;

  // One-time migration from the old persistent browser storage. Keeping the
  // demo password per tab avoids leaving it on disk across browser restarts.
  const legacyPassword = localStorage.getItem(STORAGE_KEY) || '';
  if (legacyPassword) {
    sessionStorage.setItem(STORAGE_KEY, legacyPassword);
    localStorage.removeItem(STORAGE_KEY);
  }
  return legacyPassword;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [initialPassword] = useState(restorePassword);
  const [password, setPassword] = useState(initialPassword);
  const [authState, setAuthState] = useState<'checking' | 'authenticated' | 'unauthenticated'>(
    initialPassword ? 'checking' : 'unauthenticated',
  );

  useEffect(() => {
    if (!initialPassword) return undefined;

    let cancelled = false;
    const validateRestoredPassword = async () => {
      try {
        const response = await fetch('/api/auth/check', {
          headers: { 'x-password': initialPassword },
        });
        if (cancelled) return;
        if (response.ok) {
          setAuthState('authenticated');
          return;
        }
      } catch {
        if (cancelled) return;
      }

      sessionStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(STORAGE_KEY);
      setPassword('');
      setAuthState('unauthenticated');
    };

    void validateRestoredPassword();
    return () => {
      cancelled = true;
    };
  }, [initialPassword]);

  const isLoggedIn = authState === 'authenticated';
  const isChecking = authState === 'checking';

  const login = useCallback((pw: string) => {
    sessionStorage.setItem(STORAGE_KEY, pw);
    localStorage.removeItem(STORAGE_KEY);
    setPassword(pw);
    setAuthState('authenticated');
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_KEY);
    setPassword('');
    setAuthState('unauthenticated');
    window.location.hash = '/login';
  }, []);

  return (
    <AuthContext.Provider value={{ password, isLoggedIn, isChecking, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
