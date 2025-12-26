import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../../src/contexts/AuthProvider'
import { LanguageProvider } from '../../src/contexts/LanguageContext'

// Custom render function that includes providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string
  initialAuthState?: {
    isAuthenticated: boolean
    user?: any
    token?: string
  }
}

function AllTheProviders({ children, initialAuthState }: { children: React.ReactNode; initialAuthState?: any }) {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <AuthProvider>
          {children}
        </AuthProvider>
      </BrowserRouter>
    </LanguageProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  const { route = '/', initialAuthState, ...renderOptions } = options

  // Set up route if provided
  if (route !== '/') {
    window.history.pushState({}, 'Test page', route)
  }

  return render(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders initialAuthState={initialAuthState}>
        {children}
      </AllTheProviders>
    ),
    ...renderOptions,
  })
}

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }

// Test data factories
export const createMockUser = (overrides = {}) => ({
  id: '1',
  email: 'test@example.com',
  full_name: 'Test User',
  ...overrides,
})

export const createMockRecipe = (overrides = {}) => ({
  id: 1,
  title: 'Test Recipe',
  description: 'A test recipe',
  ingredients: [{ name: 'Flour', amount: '1 cup' }],
  instructions: ['Mix ingredients', 'Bake'],
  preparation_time: 15,
  cooking_time: 30,
  servings: 4,
  difficulty_level: 'Easy',
  user_id: '1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  is_public: true,
  ...overrides,
})

export const createMockLoginResponse = (overrides = {}) => ({
  access_token: 'mock-jwt-token',
  user: createMockUser(),
  ...overrides,
})

// Common test helpers
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0))
}

export const mockLocalStorage = () => {
  const store: Record<string, string> = {}
  
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key])
    }),
  }
}
