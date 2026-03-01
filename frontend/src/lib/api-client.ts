import { API_URL } from '../config';

class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

interface User {
  id: string;
  email: string;
  full_name?: string;
  is_superuser?: boolean;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  uuid?: string;
}

interface Tag {
  id: number;
  name: string;
  uuid: string;
  recipe_counter: number;
  category: string;
  created_at: string;
  updated_at: string;
}

interface Recipe {
  id: number;
  title: string;
  description: string;
  ingredients: Array<{ name: string; amount: string }>;
  instructions: string[];
  preparation_time: number;
  cooking_time: number;
  servings: number;
  difficulty_level: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  is_public: boolean;
  image_url?: string;
  tags: Tag[];
}

interface LoginResponse {
  access_token: string;
  user: User;
}

interface PaginatedResponse<T> {
  recipes: T[];
  total: number;
  limit: number;
  offset: number;
}

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('authToken');
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Requested-With': 'XMLHttpRequest', // CSRF protection
      ...(options.headers as Record<string, string> || {}),
    };

    // Always check localStorage for the latest token
    const currentToken = this.token || localStorage.getItem('authToken');
    
    if (currentToken) {
      headers['Authorization'] = `Bearer ${currentToken}`;
      if (process.env.NODE_ENV === 'development') {
        console.log('API request with authentication');
      }
    } else {
      if (process.env.NODE_ENV === 'development') {
        console.log('API request without authentication');
      }
    }

    const url = `${API_URL}${endpoint}`;
    console.log('Making API request to:', url, 'API_URL:', API_URL, 'endpoint:', endpoint);
    
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Include cookies for CSRF protection
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(error.detail || 'An error occurred');
    }

    // For 204 No Content responses (like DELETE), return void
    if (response.status === 204) {
      return undefined as T;
    }

    // For other responses, try to parse JSON
    try {
      return await response.json();
    } catch (error) {
      // If there's no JSON body, return undefined
      return undefined as T;
    }
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await this.request<LoginResponse>('/users/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });
    this.token = response.access_token;
    localStorage.setItem('authToken', response.access_token);
    return response;
  }

  async register(email: string, password: string, fullName?: string): Promise<void> {
    await this.request('/users/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  async logout(): Promise<void> {
    this.token = null;
    localStorage.removeItem('authToken');
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/users/me');
  }

  // Recipe endpoints
  async getRecipes(limit: number = 100, offset: number = 0): Promise<Recipe[]> {
    const response = await this.request<PaginatedResponse<Recipe>>(`/recipes/?limit=${limit}&offset=${offset}`);
    return response.recipes;
  }

  async getMyRecipes(): Promise<Recipe[]> {
    const response = await this.request<{ recipes: Recipe[] }>('/recipes/my');
    return response.recipes;
  }

  async getRecipesPaginated(limit: number = 100, offset: number = 0): Promise<PaginatedResponse<Recipe>> {
    return this.request<PaginatedResponse<Recipe>>(`/recipes/?limit=${limit}&offset=${offset}`);
  }

  async getRecipe(recipeId: number): Promise<Recipe> {
    return this.request<Recipe>(`/recipes/${recipeId}`);
  }

  async createRecipe(data: Omit<Recipe, 'id' | 'created_at' | 'updated_at' | 'user_id' | 'tags'> & { tag_ids?: number[] }): Promise<Recipe> {
    return this.request<Recipe>('/recipes/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateRecipe(recipeId: number, data: Partial<Omit<Recipe, 'id' | 'created_at' | 'updated_at' | 'user_id' | 'tags'>> & { tag_ids?: number[] }): Promise<Recipe> {
    return this.request<Recipe>(`/recipes/${recipeId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteRecipe(recipeId: number): Promise<void> {
    return this.request<void>(`/recipes/${recipeId}`, {
      method: 'DELETE',
    });
  }

  async exportRecipeToPdf(recipeId: number): Promise<Blob> {
    // Always check localStorage for the latest token
    const currentToken = this.token || localStorage.getItem('authToken');
    
    const response = await fetch(`${API_URL}/recipes/${recipeId}/export/pdf`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${currentToken}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to export recipe' }));
      throw new ApiError(errorData.detail || 'Failed to export recipe');
    }

    return response.blob();
  }

  async exportRecipeToJson(recipeId: number): Promise<Recipe> {
    return this.request<Recipe>(`/recipes/${recipeId}/export/json`, {
      method: 'GET',
    });
  }

  // Tag endpoints
  async getAllTags(): Promise<Tag[]> {
    const response = await this.request<{ tags: Tag[], grouped_tags: Record<string, Tag[]>, total: number, limit: number, offset: number }>('/tags/');
    return response.tags;
  }

  async searchTags(query: string, limit = 10): Promise<Tag[]> {
    const response = await this.request<{ tags: Tag[], total: number, limit: number, offset: number }>(`/tags/search?name=${encodeURIComponent(query)}&limit=${limit}`);
    return response.tags;
  }

  async getPopularTags(limit = 10): Promise<Tag[]> {
    const response = await this.request<{ tags: Tag[], total: number, limit: number, offset: number }>(`/tags/popular?limit=${limit}`);
    return response.tags;
  }

  async getTagsForRecipe(recipeId: number): Promise<Tag[]> {
    return this.request<Tag[]>(`/tags/recipes/${recipeId}/tags`);
  }

  async updateRecipeTags(recipeId: number, addTagIds: number[] = [], removeTagIds: number[] = []): Promise<any> {
    return this.request<any>(`/tags/recipes/${recipeId}/tags`, {
      method: 'PUT',
      body: JSON.stringify({
        add_tag_ids: addTagIds,
        remove_tag_ids: removeTagIds
      })
    });
  }

  // Admin endpoints
  async getAdminTag(tagId: number): Promise<Tag> {
    return this.request<Tag>(`/admins/tags/${tagId}`);
  }

  async getAdminTagByUuid(tagUuid: string): Promise<Tag> {
    return this.request<Tag>(`/admins/tags/uuid/${tagUuid}`);
  }

  async getAdminTagByName(tagName: string): Promise<Tag> {
    return this.request<Tag>(`/admins/tags/name/${tagName}`);
  }

  async createAdminTag(name: string, category: string): Promise<Tag> {
    return this.request<Tag>('/admins/tags/', {
      method: 'POST',
      body: JSON.stringify({ name, category })
    });
  }

  async updateAdminTag(tagId: number, name: string, category: string): Promise<Tag> {
    return this.request<Tag>(`/admins/tags/${tagId}`, {
      method: 'PUT',
      body: JSON.stringify({ name, category })
    });
  }

  async deleteAdminTag(tagId: number): Promise<{ tag_name: string; recipes_affected: number }> {
    return this.request<{ tag_name: string; recipes_affected: number }>(`/admins/tags/${tagId}`, {
      method: 'DELETE',
    });
  }

  async testDbConnection(): Promise<any> {
    return this.request<any>('/admins/test-db-connection');
  }

  async testConfig(): Promise<any> {
    return this.request<any>('/admins/config-test');
  }

  async testSetup(): Promise<any> {
    return this.request<any>('/admins/test-setup');
  }

  // Admin User Management
  async getAllUsers(limit = 100, offset = 0): Promise<{ users: User[], total: number }> {
    return this.request<{ users: User[], total: number }>(`/users/?limit=${limit}&offset=${offset}`);
  }

  async getUserById(userId: string | number): Promise<User> {
    return this.request<User>(`/users/${userId}`);
  }

  async updateUser(userId: string | number, data: { email?: string, full_name?: string, is_active?: boolean }): Promise<User> {
    return this.request<User>(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async updateUserPassword(userId: string | number, password: string): Promise<void> {
    return this.request<void>(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ password }),
    });
  }

  async setUserSuperuser(userId: string | number, is_superuser: boolean): Promise<User> {
    return this.request<User>(`/users/${userId}/set-superuser`, {
      method: 'PUT',
      body: JSON.stringify({ is_superuser }),
    });
  }

  async deleteUser(userId: string | number, transferToAdminId?: string | number): Promise<void> {
    const queryParams = transferToAdminId ? `?transfer_to_admin_id=${transferToAdminId}` : '';
    return this.request<void>(`/users/${userId}${queryParams}`, {
      method: 'DELETE',
    });
  }

  // Admin Recipe Management (get all/edit/delete any recipe)
  async getAllRecipesForAdmin(limit: number = 1000, offset: number = 0): Promise<Recipe[]> {
    const response = await this.request<PaginatedResponse<Recipe>>(`/admins/recipes/?limit=${limit}&offset=${offset}`);
    return response.recipes;
  }

  async adminUpdateRecipe(recipeId: number, data: any): Promise<Recipe> {
    return this.request<Recipe>(`/recipes/${recipeId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async adminDeleteRecipe(recipeId: number): Promise<void> {
    return this.request<void>(`/recipes/${recipeId}`, {
      method: 'DELETE',
    });
  }

  // Transfer recipes from one user to another
  async transferUserRecipes(fromUserId: string | number, toUserId: string | number): Promise<number> {
    // Get all recipes and filter by user_id, then update each one
    const allRecipes = await this.getRecipes(1000);
    const userRecipes = allRecipes.filter(r => r.user_id === String(fromUserId));
    
    // Update each recipe's user_id
    for (const recipe of userRecipes) {
      await this.adminUpdateRecipe(recipe.id, {
        ...recipe,
        user_id: String(toUserId)
      });
    }
    
    return userRecipes.length;
  }

  // AI-related methods
  async testAI(data: AITestRequest): Promise<AITestResponse> {
    return this.request<AITestResponse>('/ai/test', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async suggestTags(data: TagSuggestionRequest): Promise<TagSuggestionResponse> {
    return this.request<TagSuggestionResponse>('/ai/suggest-tags', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async searchNaturalLanguage(query: string): Promise<NaturalLanguageSearchResponse> {
    return this.request<NaturalLanguageSearchResponse>('/ai/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  async calculateNutrition(ingredients: Ingredient[]): Promise<NutritionResponse> {
    return this.request<NutritionResponse>('/ai/nutrition', {
      method: 'POST',
      body: JSON.stringify({ ingredients }),
    });
  }

  // LLM Configuration endpoints (admin only)
  async getAllLLMConfigs(): Promise<LLMConfig[]> {
    return this.request<LLMConfig[]>('/llm-configs/');
  }

  async getGlobalLLMConfig(): Promise<LLMConfig | null> {
    return this.request<LLMConfig | null>('/llm-configs/global');
  }

  async getServiceLLMConfig(serviceName: string): Promise<LLMConfig | null> {
    return this.request<LLMConfig | null>(`/llm-configs/service/${serviceName}`);
  }

  async getEffectiveLLMConfig(serviceName: string): Promise<EffectiveLLMConfig> {
    return this.request<EffectiveLLMConfig>(`/llm-configs/effective/${serviceName}`);
  }

  async createLLMConfig(data: LLMConfigCreate): Promise<LLMConfig> {
    return this.request<LLMConfig>('/llm-configs/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateLLMConfig(configId: number, data: Partial<LLMConfigUpdate>): Promise<LLMConfig> {
    return this.request<LLMConfig>(`/llm-configs/${configId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteLLMConfig(configId: number): Promise<void> {
    return this.request<void>(`/llm-configs/${configId}`, {
      method: 'DELETE',
    });
  }
}

// AI-related types
interface AITestRequest {
  model: string;
  system_prompt?: string;
  user_prompt: string;
  temperature?: number;
  max_tokens?: number;
  response_format?: 'json' | null;
}

interface AITestResponse {
  content: any;
  tokens_used: {
    prompt: number;
    completion: number;
    total: number;
  };
  model: string;
  finish_reason: string;
  estimated_cost: number;
}

interface TagSuggestionRequest {
  recipe_title: string;
  ingredients: string[];
  existing_tags?: string[];
}

interface TagSuggestionResponse {
  suggested_tags: string[];
  confidence: number;
}

interface NaturalLanguageSearchResponse {
  keywords?: string[];
  tags?: string[];
  max_prep_time?: number;
  max_cook_time?: number;
  difficulty?: string;
}

interface Ingredient {
  name: string;
  amount: string;
}

interface NutritionResponse {
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
}

// LLM Configuration types
interface LLMConfig {
  id: number;
  uuid: string;
  config_type: 'GLOBAL' | 'SERVICE';
  service_name: string | null;
  provider: 'OPENAI' | 'ANTHROPIC' | 'GOOGLE';
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string | null;
  user_prompt_template: string | null;
  response_format: string | null;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
  description: string | null;
}

interface LLMConfigCreate {
  config_type: 'GLOBAL' | 'SERVICE';
  service_name?: string;
  provider: 'OPENAI' | 'ANTHROPIC' | 'GOOGLE';
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt?: string;
  user_prompt_template?: string;
  response_format?: string;
  description?: string;
  is_active?: boolean;
}

interface LLMConfigUpdate {
  config_type?: 'GLOBAL' | 'SERVICE';
  service_name?: string;
  provider?: 'OPENAI' | 'ANTHROPIC' | 'GOOGLE';
  model?: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  user_prompt_template?: string;
  response_format?: string;
  description?: string;
  is_active?: boolean;
}

interface EffectiveLLMConfig {
  provider: string;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string | null;
  user_prompt_template: string | null;
  response_format: string | null;
  source: Record<string, any>;
}

export const apiClient = new ApiClient();
export { 
  ApiError, 
  type Recipe, 
  type Tag, 
  type User, 
  type LoginResponse, 
  type PaginatedResponse,
  type AITestRequest,
  type AITestResponse,
  type TagSuggestionRequest,
  type TagSuggestionResponse,
  type NaturalLanguageSearchResponse,
  type Ingredient,
  type NutritionResponse,
  type LLMConfig,
  type LLMConfigCreate,
  type LLMConfigUpdate,
  type EffectiveLLMConfig
};