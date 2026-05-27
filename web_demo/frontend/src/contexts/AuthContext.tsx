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
  const [password, setPassword] = useState(() => localStorage.getItem(STORAGE_KEY) || '');

  const isLoggedIn = !!password;

  const login = useCallback((pw: string) => {
    localStorage.setItem(STORAGE_KEY, pw);
    setPassword(pw);
  }, []);

  const logout = useCallback(() => {
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
