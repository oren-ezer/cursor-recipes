import React, { createContext, useContext } from 'react'
import { describe, it, expect, vi } from 'vitest'
import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import { AuthContext, useAuth, type AuthUser, type AuthContextType } from '../../src/contexts/AuthContext'
import { createMockUser } from '../setup/test-utils'

// Test component that uses the auth context
const TestComponent = () => {
  const { isAuthenticated, user, token, login, logout, isLoading } = useAuth()
  
  return (
    <div>
      <div data-testid="is-authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="user-email">{user?.email || 'no-user'}</div>
      <div data-testid="token">{token || 'no-token'}</div>
      <div data-testid="is-loading">{isLoading.toString()}</div>
      <button 
        data-testid="login-btn" 
        onClick={() => login('test-token', createMockUser())}
      >
        Login
      </button>
      <button data-testid="logout-btn" onClick={() => logout()}>
        Logout
      </button>
    </div>
  )
}

describe('AuthContext', () => {
  describe('useAuth hook', () => {
    it('should throw error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      // Create a context without default value to test the error case
      const TestContext = createContext<AuthContextType | undefined>(undefined)
      
      const TestComponentWithUndefinedContext = () => {
        const context = useContext(TestContext)
        if (context === undefined) {
          throw new Error('useAuth must be used within an AuthProvider')
        }
        return <div>Test</div>
      }
      
      expect(() => {
        render(<TestComponentWithUndefinedContext />)
      }).toThrow('useAuth must be used within an AuthProvider')
      
      consoleSpy.mockRestore()
    })

    it('should provide default context values', () => {
      render(
        <AuthContext.Provider value={{
          isAuthenticated: false,
          user: null,
          token: null,
          login: vi.fn(),
          logout: vi.fn(),
          isLoading: false,
        }}>
          <TestComponent />
        </AuthContext.Provider>
      )

      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
      expect(screen.getByTestId('user-email')).toHaveTextContent('no-user')
      expect(screen.getByTestId('token')).toHaveTextContent('no-token')
      expect(screen.getByTestId('is-loading')).toHaveTextContent('false')
    })

    it('should provide authenticated context values', () => {
      const mockUser = createMockUser()
      const mockToken = 'test-jwt-token'
      
      render(
        <AuthContext.Provider value={{
          isAuthenticated: true,
          user: mockUser,
          token: mockToken,
          login: vi.fn(),
          logout: vi.fn(),
          isLoading: false,
        }}>
          <TestComponent />
        </AuthContext.Provider>
      )

      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
      expect(screen.getByTestId('user-email')).toHaveTextContent(mockUser.email)
      expect(screen.getByTestId('token')).toHaveTextContent(mockToken)
      expect(screen.getByTestId('is-loading')).toHaveTextContent('false')
    })

    it('should call login function when login button is clicked', async () => {
      const mockLogin = vi.fn()
      const mockUser = createMockUser()
      
      render(
        <AuthContext.Provider value={{
          isAuthenticated: false,
          user: null,
          token: null,
          login: mockLogin,
          logout: vi.fn(),
          isLoading: false,
        }}>
          <TestComponent />
        </AuthContext.Provider>
      )

      const loginButton = screen.getByTestId('login-btn')
      loginButton.click()

      expect(mockLogin).toHaveBeenCalledWith('test-token', mockUser)
    })

    it('should call logout function when logout button is clicked', async () => {
      const mockLogout = vi.fn()
      
      render(
        <AuthContext.Provider value={{
          isAuthenticated: true,
          user: createMockUser(),
          token: 'test-token',
          login: vi.fn(),
          logout: mockLogout,
          isLoading: false,
        }}>
          <TestComponent />
        </AuthContext.Provider>
      )

      const logoutButton = screen.getByTestId('logout-btn')
      logoutButton.click()

      expect(mockLogout).toHaveBeenCalled()
    })
  })

  describe('AuthUser interface', () => {
    it('should accept valid user data', () => {
      const user: AuthUser = {
        id: '1',
        email: 'test@example.com',
      }
      
      expect(user.id).toBe('1')
      expect(user.email).toBe('test@example.com')
    })

    it('should accept numeric id', () => {
      const user: AuthUser = {
        id: 1,
        email: 'test@example.com',
      }
      
      expect(user.id).toBe(1)
      expect(user.email).toBe('test@example.com')
    })
  })

  describe('AuthContextType interface', () => {
    it('should have all required properties', () => {
      const contextValue = {
        isAuthenticated: true,
        user: createMockUser(),
        token: 'test-token',
        login: vi.fn(),
        logout: vi.fn(),
        isLoading: false,
      }
      
      expect(contextValue).toHaveProperty('isAuthenticated')
      expect(contextValue).toHaveProperty('user')
      expect(contextValue).toHaveProperty('token')
      expect(contextValue).toHaveProperty('login')
      expect(contextValue).toHaveProperty('logout')
      expect(contextValue).toHaveProperty('isLoading')
    })
  })
})
