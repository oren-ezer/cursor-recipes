import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { apiClient, ApiError } from '../../src/lib/api-client'
import { createMockUser, createMockRecipe, createMockLoginResponse } from '../setup/test-utils'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('ApiClient', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    // Clear localStorage mock
    vi.mocked(localStorage.clear).mockClear()
    vi.mocked(localStorage.getItem).mockReturnValue(null)
    vi.mocked(localStorage.setItem).mockClear()
    vi.mocked(localStorage.removeItem).mockClear()
    apiClient.setToken(null)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Authentication', () => {
    it('should login successfully', async () => {
      const mockResponse = createMockLoginResponse()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await apiClient.login('test@example.com', 'password')

      expect(result).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/users/token',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/x-www-form-urlencoded',
          }),
          body: 'username=test%40example.com&password=password',
        })
      )
    })

    it('should register successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      await apiClient.register('test@example.com', 'password', 'Test User')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/users/register',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password',
            full_name: 'Test User',
          }),
        })
      )
    })

    it('should logout and clear token', async () => {
      // Set up initial token
      vi.mocked(localStorage.setItem).mockImplementation(() => {})
      vi.mocked(localStorage.removeItem).mockImplementation(() => {})
      apiClient.setToken('test-token')

      await apiClient.logout()

      expect(localStorage.removeItem).toHaveBeenCalledWith('authToken')
      // Note: We can't directly test the private token property, but we can test the effect
    })

    it('should get current user', async () => {
      const mockUser = createMockUser()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      })

      // Set the token before making the request
      apiClient.setToken('test-token')

      const result = await apiClient.getCurrentUser()

      expect(result).toEqual(mockUser)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/users/me',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })
  })

  describe('Recipe Operations', () => {
    beforeEach(() => {
      apiClient.setToken('test-token')
    })

    it('should get recipes', async () => {
      const mockRecipes = [createMockRecipe()]
      const mockResponse = {
        recipes: mockRecipes,
        total: 1,
        limit: 10,
        offset: 0,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await apiClient.getRecipes(10, 0)

      expect(result).toEqual(mockRecipes)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/recipes/?limit=10&offset=0',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })

    it('should get my recipes', async () => {
      const mockRecipes = [createMockRecipe()]
      const mockResponse = { recipes: mockRecipes }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await apiClient.getMyRecipes()

      expect(result).toEqual(mockRecipes)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/recipes/my',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })

    it('should get single recipe', async () => {
      const mockRecipe = createMockRecipe()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecipe,
      })

      const result = await apiClient.getRecipe(1)

      expect(result).toEqual(mockRecipe)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/recipes/1',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })

    it('should create recipe', async () => {
      const mockRecipe = createMockRecipe()
      const recipeData = {
        title: 'New Recipe',
        description: 'A new recipe',
        ingredients: [{ name: 'Flour', amount: '1 cup' }],
        instructions: ['Mix', 'Bake'],
        preparation_time: 15,
        cooking_time: 30,
        servings: 4,
        difficulty_level: 'Easy' as const,
        is_public: true,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecipe,
      })

      const result = await apiClient.createRecipe(recipeData)

      expect(result).toEqual(mockRecipe)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/recipes/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(recipeData),
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })

    it('should update recipe', async () => {
      const mockRecipe = createMockRecipe({ title: 'Updated Recipe' })
      const updateData = { title: 'Updated Recipe' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecipe,
      })

      const result = await apiClient.updateRecipe(1, updateData)

      expect(result).toEqual(mockRecipe)
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/recipes/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })

    it('should delete recipe', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      await apiClient.deleteRecipe(1)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/recipes/1',
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })
  })

  describe('Error Handling', () => {
    it('should throw ApiError on non-ok response', async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Bad request' }),
      }
      mockFetch.mockResolvedValueOnce(mockResponse)

      await expect(apiClient.getRecipes()).rejects.toThrow(ApiError)
    })

    it('should throw generic error when response has no detail', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        json: async () => ({}),
      }
      mockFetch.mockResolvedValueOnce(mockResponse)

      await expect(apiClient.getRecipes()).rejects.toThrow(ApiError)
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(apiClient.getRecipes()).rejects.toThrow('Network error')
    })
  })

  describe('Token Management', () => {
    it('should include token in requests when available', async () => {
      apiClient.setToken('test-token')
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      await apiClient.getRecipes()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      )
    })

    it('should not include token in requests when not available', async () => {
      apiClient.setToken(null)
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      await apiClient.getRecipes()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.any(String),
          }),
        })
      )
    })

    it('should fall back to localStorage token', async () => {
      vi.mocked(localStorage.getItem).mockReturnValue('localstorage-token')
      apiClient.setToken(null)
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      await apiClient.getRecipes()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer localstorage-token',
          }),
        })
      )
    })
  })
})
