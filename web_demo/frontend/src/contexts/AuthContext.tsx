import { createContext, useContext, useState, useCallback } from 'react';

const STORAGE_KEY = 'labsafe_password';

interface AuthContextValue {
  password: string;
  isLoggedIn: boolean;
  login: (pw: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  password: '',
  isLoggedIn: false,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [password, setPassword] = useState(() => {
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
  });

  const isLoggedIn = !!password;

  const login = useCallback((pw: string) => {
    sessionStorage.setItem(STORAGE_KEY, pw);
    localStorage.removeItem(STORAGE_KEY);
    setPassword(pw);
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_KEY);
    setPassword('');
    window.location.hash = '/login';
  }, []);

  return (
    <AuthContext.Provider value={{ password, isLoggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
