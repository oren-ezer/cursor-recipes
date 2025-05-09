import React, { useState, useEffect, type ReactNode } from 'react';
import { AuthContext, type AuthUser } from './AuthContext';
import { jwtDecode } from 'jwt-decode'; // For decoding JWT to get user info (optional)

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true); // Start with loading true

  useEffect(() => {
    // Check for token in localStorage on initial load
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      try {
        // Optional: Decode token to get user info and check expiry
        // This is a basic example; in production, you'd also verify the token against a backend
        // or refresh it if it's about to expire.
        const decodedToken = jwtDecode<any>(storedToken); // Type assertion for decoded structure
        const currentTime = Date.now() / 1000;

        if (decodedToken.exp > currentTime) {
          setToken(storedToken);
          // Assuming your JWT 'sub' is email and you have a 'user_id' claim
          // You might fetch full user details from an API here instead of relying solely on JWT claims
          setUser({ id: decodedToken.user_id, email: decodedToken.sub }); 
        } else {
          // Token expired
          localStorage.removeItem('authToken');
        }
      } catch (error) {
        console.error("Failed to decode token:", error);
        localStorage.removeItem('authToken'); // Clear invalid token
      }
    }
    setIsLoading(false); // Finished initial auth check
  }, []);

  const login = async (newToken: string, userData?: AuthUser) => {
    localStorage.setItem('authToken', newToken);
    setToken(newToken);
    if (userData) {
      setUser(userData);
    } else {
      // If userData is not passed directly, decode from token
      try {
        const decodedToken = jwtDecode<any>(newToken);
        setUser({ id: decodedToken.user_id, email: decodedToken.sub });
      } catch (error) {
        console.error("Failed to decode token on login:", error);
        // Handle error, maybe clear token and user
        setUser(null);
        setToken(null);
        localStorage.removeItem('authToken');
      }
    }
  };

  const logout = async () => {
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      isAuthenticated: !!token,
      user,
      token,
      login,
      logout,
      isLoading
    }}>
      {children}
    </AuthContext.Provider>
  );
}; 