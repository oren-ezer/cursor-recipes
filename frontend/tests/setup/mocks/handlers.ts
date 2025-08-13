import { rest } from 'msw'

const API_BASE = 'http://localhost:8000/api/v1'

// Mock data
const mockUser = {
  id: '1',
  email: 'test@example.com',
  full_name: 'Test User',
}

const mockRecipes = [
  {
    id: 1,
    title: 'Test Recipe 1',
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
  },
  {
    id: 2,
    title: 'Test Recipe 2',
    description: 'Another test recipe',
    ingredients: [{ name: 'Sugar', amount: '1/2 cup' }],
    instructions: ['Mix', 'Cook'],
    preparation_time: 10,
    cooking_time: 20,
    servings: 2,
    difficulty_level: 'Medium',
    user_id: '1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    is_public: false,
  },
]

export const handlers = [
  // Auth endpoints
  rest.post(`${API_BASE}/users/token`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock-jwt-token',
        user: mockUser,
      })
    )
  }),

  rest.post(`${API_BASE}/users/register`, (req, res, ctx) => {
    return res(ctx.status(201))
  }),

  rest.get(`${API_BASE}/users/me`, (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockUser))
  }),

  // Recipe endpoints
  rest.get(`${API_BASE}/recipes`, (req, res, ctx) => {
    const url = new URL(req.url)
    const limit = parseInt(url.searchParams.get('limit') || '10')
    const offset = parseInt(url.searchParams.get('offset') || '0')
    
    const publicRecipes = mockRecipes.filter(recipe => recipe.is_public)
    const paginatedRecipes = publicRecipes.slice(offset, offset + limit)
    
    return res(
      ctx.status(200),
      ctx.json({
        recipes: paginatedRecipes,
        total: publicRecipes.length,
        limit,
        offset,
      })
    )
  }),

  rest.get(`${API_BASE}/recipes/my`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        recipes: mockRecipes,
        total: mockRecipes.length,
        limit: 10,
        offset: 0,
      })
    )
  }),

  rest.get(`${API_BASE}/recipes/:id`, (req, res, ctx) => {
    const { id } = req.params
    const recipe = mockRecipes.find(r => r.id === parseInt(id as string))
    
    if (!recipe) {
      return res(ctx.status(404), ctx.json({ detail: 'Recipe not found' }))
    }
    
    return res(ctx.status(200), ctx.json(recipe))
  }),

  rest.post(`${API_BASE}/recipes`, (req, res, ctx) => {
    const newRecipe = {
      id: 3,
      ...req.body,
      user_id: '1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    return res(ctx.status(201), ctx.json(newRecipe))
  }),

  rest.put(`${API_BASE}/recipes/:id`, (req, res, ctx) => {
    const { id } = req.params
    const recipe = mockRecipes.find(r => r.id === parseInt(id as string))
    
    if (!recipe) {
      return res(ctx.status(404), ctx.json({ detail: 'Recipe not found' }))
    }
    
    const updatedRecipe = { ...recipe, ...req.body, updated_at: new Date().toISOString() }
    return res(ctx.status(200), ctx.json(updatedRecipe))
  }),

  rest.delete(`${API_BASE}/recipes/:id`, (req, res, ctx) => {
    const { id } = req.params
    const recipe = mockRecipes.find(r => r.id === parseInt(id as string))
    
    if (!recipe) {
      return res(ctx.status(404), ctx.json({ detail: 'Recipe not found' }))
    }
    
    return res(ctx.status(204))
  }),
]
