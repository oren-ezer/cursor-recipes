import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import '@testing-library/jest-dom'
import { render, screen, fireEvent } from '../setup/test-utils'
import RecipeCard from '../../src/components/RecipeCard'
import { createMockRecipe } from '../setup/test-utils'

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const renderRecipeCard = (props: any) => {
  return render(<RecipeCard {...props} />)
}

describe('RecipeCard', () => {
  const defaultRecipe = createMockRecipe()

  beforeEach(() => {
    mockNavigate.mockClear()
  })

  describe('Rendering', () => {
    it('should render recipe information correctly', () => {
      renderRecipeCard({ recipe: defaultRecipe })

      expect(screen.getByText(defaultRecipe.title)).toBeInTheDocument()
      expect(screen.getByText(defaultRecipe.description)).toBeInTheDocument()
      expect(screen.getByText('1 ingredients')).toBeInTheDocument()
      expect(screen.getByText(defaultRecipe.difficulty_level)).toBeInTheDocument()
    })

    it('should render with default variant', () => {
      renderRecipeCard({ recipe: defaultRecipe })

      expect(screen.getByText('View Recipe')).toBeInTheDocument()
    })

    it('should render with my-recipes variant', () => {
      renderRecipeCard({ 
        recipe: defaultRecipe, 
        variant: 'my-recipes',
        onDelete: vi.fn()
      })

      expect(screen.getByText('View')).toBeInTheDocument()
      expect(screen.getByText('Edit')).toBeInTheDocument()
      expect(screen.getByText('Delete')).toBeInTheDocument()
    })

    it('should render with compact variant', () => {
      renderRecipeCard({ 
        recipe: defaultRecipe, 
        variant: 'compact'
      })

      expect(screen.getByText('View Recipe')).toBeInTheDocument()
      // Compact variant should show less content
      expect(screen.queryByText('Prep: 15m')).not.toBeInTheDocument()
    })

    it('should hide actions when showActions is false', () => {
      renderRecipeCard({ 
        recipe: defaultRecipe, 
        showActions: false
      })

      expect(screen.queryByText('View Recipe')).not.toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('should navigate to recipe detail when View Recipe is clicked', () => {
      renderRecipeCard({ recipe: defaultRecipe })

      fireEvent.click(screen.getByText('View Recipe'))

      expect(mockNavigate).toHaveBeenCalledWith(`/recipes/${defaultRecipe.id}`)
    })

    it('should navigate to recipe edit when Edit is clicked', () => {
      renderRecipeCard({ 
        recipe: defaultRecipe, 
        variant: 'my-recipes'
      })

      fireEvent.click(screen.getByText('Edit'))

      expect(mockNavigate).toHaveBeenCalledWith(`/recipes/${defaultRecipe.id}/edit`)
    })

    it('should call onDelete when Delete is clicked', () => {
      const mockOnDelete = vi.fn()
      renderRecipeCard({ 
        recipe: defaultRecipe, 
        variant: 'my-recipes',
        onDelete: mockOnDelete
      })

      fireEvent.click(screen.getByText('Delete'))

      expect(mockOnDelete).toHaveBeenCalledWith(defaultRecipe)
    })

    it('should call onView when provided', () => {
      const mockOnView = vi.fn()
      renderRecipeCard({ 
        recipe: defaultRecipe, 
        onView: mockOnView
      })

      fireEvent.click(screen.getByText('View Recipe'))

      expect(mockOnView).toHaveBeenCalledWith(defaultRecipe)
      expect(mockNavigate).not.toHaveBeenCalled()
    })

    it('should call onEdit when provided', () => {
      const mockOnEdit = vi.fn()
      renderRecipeCard({ 
        recipe: defaultRecipe, 
        variant: 'my-recipes',
        onEdit: mockOnEdit
      })

      fireEvent.click(screen.getByText('Edit'))

      expect(mockOnEdit).toHaveBeenCalledWith(defaultRecipe)
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  describe('Display Logic', () => {
    it('should format time correctly', () => {
      const recipeWithLongTime = createMockRecipe({
        preparation_time: 90, // 1h 30m
        cooking_time: 120, // 2h
      })

      renderRecipeCard({ recipe: recipeWithLongTime })

      expect(screen.getByText('Prep: 1h 30m')).toBeInTheDocument()
      expect(screen.getByText('Cook: 2h')).toBeInTheDocument()
    })

    it('should format short time correctly', () => {
      const recipeWithShortTime = createMockRecipe({
        preparation_time: 30,
        cooking_time: 45,
      })

      renderRecipeCard({ recipe: recipeWithShortTime })

      expect(screen.getByText('Prep: 30m')).toBeInTheDocument()
      expect(screen.getByText('Cook: 45m')).toBeInTheDocument()
    })

    it('should show difficulty color correctly', () => {
      const easyRecipe = createMockRecipe({ difficulty_level: 'Easy' })
      const mediumRecipe = createMockRecipe({ difficulty_level: 'Medium' })
      const hardRecipe = createMockRecipe({ difficulty_level: 'Hard' })

      const { rerender } = renderRecipeCard({ recipe: easyRecipe })
      expect(screen.getByText('Easy')).toHaveClass('text-green-600')

      rerender(<RecipeCard recipe={mediumRecipe} />)
      expect(screen.getByText('Medium')).toHaveClass('text-yellow-600')

      rerender(<RecipeCard recipe={hardRecipe} />)
      expect(screen.getByText('Hard')).toHaveClass('text-red-600')
    })

    it('should show image indicator when recipe has image', () => {
      const recipeWithImage = createMockRecipe({
        image_url: 'https://example.com/image.jpg'
      })

      renderRecipeCard({ recipe: recipeWithImage })

      expect(screen.getByText('Has image')).toBeInTheDocument()
    })

    it('should not show image indicator when recipe has no image', () => {
      renderRecipeCard({ recipe: defaultRecipe })

      expect(screen.queryByText('Has image')).not.toBeInTheDocument()
    })
  })

  describe('Share/Unshare Actions', () => {
    it('should show share button for private recipes', () => {
      const privateRecipe = createMockRecipe({ is_public: false })
      const mockOnShare = vi.fn()

      renderRecipeCard({ 
        recipe: privateRecipe, 
        onShare: mockOnShare
      })

      expect(screen.getByText('Share')).toBeInTheDocument()
      
      fireEvent.click(screen.getByText('Share'))
      expect(mockOnShare).toHaveBeenCalledWith(privateRecipe)
    })

    it('should show unshare button for public recipes', () => {
      const publicRecipe = createMockRecipe({ is_public: true })
      const mockOnUnshare = vi.fn()

      renderRecipeCard({ 
        recipe: publicRecipe, 
        onUnshare: mockOnUnshare
      })

      expect(screen.getByText('Unshare')).toBeInTheDocument()
      
      fireEvent.click(screen.getByText('Unshare'))
      expect(mockOnUnshare).toHaveBeenCalledWith(publicRecipe)
    })

    it('should not show share button for public recipes', () => {
      const publicRecipe = createMockRecipe({ is_public: true })
      const mockOnShare = vi.fn()

      renderRecipeCard({ 
        recipe: publicRecipe, 
        onShare: mockOnShare
      })

      expect(screen.queryByText('Share')).not.toBeInTheDocument()
    })

    it('should not show unshare button for private recipes', () => {
      const privateRecipe = createMockRecipe({ is_public: false })
      const mockOnUnshare = vi.fn()

      renderRecipeCard({ 
        recipe: privateRecipe, 
        onUnshare: mockOnUnshare
      })

      expect(screen.queryByText('Unshare')).not.toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle recipe with empty description', () => {
      const recipeWithEmptyDesc = createMockRecipe({ description: '' })
      renderRecipeCard({ recipe: recipeWithEmptyDesc })

      expect(screen.getByText(recipeWithEmptyDesc.title)).toBeInTheDocument()
    })

    it('should handle recipe with no ingredients', () => {
      const recipeWithNoIngredients = createMockRecipe({ ingredients: [] })
      renderRecipeCard({ recipe: recipeWithNoIngredients })

      expect(screen.getByText('0 ingredients')).toBeInTheDocument()
    })

    it('should handle recipe with no instructions', () => {
      const recipeWithNoInstructions = createMockRecipe({ instructions: [] })
      renderRecipeCard({ recipe: recipeWithNoInstructions })

      expect(screen.getByText(recipeWithNoInstructions.title)).toBeInTheDocument()
    })
  })
})
