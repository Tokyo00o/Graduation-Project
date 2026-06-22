import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, token: null, loading: true });

  useEffect(() => {
    const token = localStorage.getItem('fuzzguard_token');
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      api.get('/auth/me').then(r => {
        setState({ user: r.data, token, loading: false });
      }).catch(() => {
        localStorage.removeItem('fuzzguard_token');
        setState({ user: null, token: null, loading: false });
      });
    } else {
      setState(s => ({ ...s, loading: false }));
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const r = await api.post('/auth/login', { email, password });
    const { access_token, user } = r.data;
    localStorage.setItem('fuzzguard_token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setState({ user, token: access_token, loading: false });
  }, []);

  const signup = useCallback(async (email: string, password: string, name: string) => {
    const r = await api.post('/auth/signup', { email, password, name });
    const { access_token, user } = r.data;
    localStorage.setItem('fuzzguard_token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setState({ user, token: access_token, loading: false });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('fuzzguard_token');
    delete api.defaults.headers.common['Authorization'];
    setState({ user: null, token: null, loading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
}
