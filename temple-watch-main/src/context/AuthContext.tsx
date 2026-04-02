import React, { createContext, useContext, useState, ReactNode } from 'react';
import { UserRole, AuthState } from '@/types/auth';

interface AuthContextType extends AuthState {
  login: (role: UserRole) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    role: null,
  });

  const login = (role: UserRole) => {
    setAuthState({ isAuthenticated: true, role });
  };

  const logout = () => {
    setAuthState({ isAuthenticated: false, role: null });
  };

  return (
    <AuthContext.Provider value={{ ...authState, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
