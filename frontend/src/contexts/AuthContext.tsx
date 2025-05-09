import { createContext, useContext } from 'react';

// Define the shape of the user object (you can expand this)
export interface AuthUser {
  id: string | number; // Or whatever your user ID type is
  email: string;
  // Add other relevant user fields, e.g., fullName, roles, etc.
}

// Define the shape of the context value
export interface AuthContextType {
  isAuthenticated: boolean;
  user: AuthUser | null;
  token: string | null;
  login: (token: string, userData?: AuthUser) => Promise<void>; // Made userData optional
  logout: () => Promise<void>; // Make logout async if it involves async ops
  isLoading: boolean; // To handle loading state, e.g., while checking initial auth status
}

// Create the context with a default value
// The default value is often null or a shape that indicates no user is authenticated.
// We provide a more complete default to satisfy TypeScript, but components should always check isLoading or isAuthenticated.
export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  token: null,
  login: async (token: string, userData?: AuthUser) => { console.warn("Login function not yet implemented in AuthProvider", token, userData) }, // Reflect optional userData
  logout: async () => { console.warn("Logout function not yet implemented in AuthProvider") },
  isLoading: true, // Assume loading initially until AuthProvider checks
});

// Custom hook to use the AuthContext (optional but recommended)
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 