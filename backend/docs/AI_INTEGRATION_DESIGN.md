# AI Integration Design Document

## Story #1000: OpenAI Library Upgrade & Architecture Design
## Story #1001: LLM Integration Planning

---

## 1. OpenAI Library Upgrade (1.101.0 → 2.8.1)

### Breaking Changes Summary
The OpenAI Python library v2.x introduced significant breaking changes:
- **Client initialization**: Now uses `OpenAI()` client instead of direct API calls
- **Async support**: Native async client with `AsyncOpenAI()`
- **Response format**: Structured response objects instead of dictionaries
- **Error handling**: New exception hierarchy
- **Streaming**: Improved streaming API

### Migration Strategy
1. Install OpenAI v2.8.1 via `uv add openai>=2.8.1`
2. Create new `AIService` to encapsulate all OpenAI interactions
3. Use async/await pattern for non-blocking LLM calls
4. Implement proper error handling for API failures

---

## 2. AI Endpoint Architecture Design

### Option A: Separate AI Service (RECOMMENDED)
**Structure:**
```
backend/src/
├── services/
│   └── ai_service.py          # Core AI service with LLM calls
├── api/v1/endpoints/
│   └── ai.py                  # AI-specific endpoints
└── models/
    └── ai_models.py           # Pydantic models for AI requests/responses
```

**Pros:**
- ✅ Clear separation of concerns
- ✅ Easy to add new AI features
- ✅ Can be rate-limited independently
- ✅ Admin-only access can be enforced at router level
- ✅ Easier to mock and test

**Cons:**
- ❌ Slightly more initial setup

### Option B: Integrate into Existing Endpoints
Add AI capabilities to existing recipe/tag endpoints

**Pros:**
- ✅ Less code duplication
- ✅ Unified API surface

**Cons:**
- ❌ Mixed concerns (AI + CRUD)
- ❌ Harder to control access
- ❌ More complex testing

### **Decision: Use Option A (Separate AI Service)**

---

## 3. LLM Integration Planning

### 3.1 Authentication & API Keys

**Storage:**
- Store OpenAI API key in environment variables (`.env`)
- Never commit keys to version control
- Add to `.env.example` for documentation

**Configuration:**
```python
# backend/src/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    OPENAI_API_KEY: str
    OPENAI_ORG_ID: Optional[str] = None
    OPENAI_DEFAULT_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.7
```

### 3.2 Supported Models

**Initial Support:**
- `gpt-4o` - Most capable, expensive
- `gpt-4o-mini` - Fast, cost-effective (default)
- `gpt-3.5-turbo` - Legacy, cheaper

**Model Selection Strategy:**
- Admin can select model via UI
- Different models for different use cases:
  - Tag suggestions: `gpt-4o-mini` (fast, cheap)
  - Recipe understanding: `gpt-4o` (better comprehension)
  - Nutrition facts: `gpt-4o-mini` (structured output)

### 3.3 Prompt Engineering

**System Prompt Structure:**
```
You are a culinary AI assistant helping with a recipe management application.
Your responses should be accurate, concise, and food-safety aware.
```

**User Prompt Templates:**
Each AI feature will have its own prompt template:
- Tag suggestions
- Recipe search
- Recipe from image
- Nutrition facts

### 3.4 Response Parsing

**Structured Output:**
Use OpenAI's JSON mode for structured responses:
```python
response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    response_format={"type": "json_object"}
)
```

**Parsing Strategy:**
1. Request JSON format in system prompt
2. Use Pydantic models to validate responses
3. Handle malformed responses with fallbacks
4. Log all AI interactions for debugging

### 3.5 Error Handling

**Error Types:**
- `AuthenticationError` - Invalid API key
- `RateLimitError` - Too many requests
- `APIConnectionError` - Network issues
- `APIError` - General API failures

**Strategy:**
```python
try:
    response = await ai_service.call_llm(...)
except RateLimitError:
    # Return cached response or friendly error
    raise HTTPException(429, "AI service temporarily unavailable")
except AuthenticationError:
    # Log critical error, alert admin
    raise HTTPException(500, "AI service misconfigured")
except APIError as e:
    # Log error, return graceful failure
    raise HTTPException(503, "AI service unavailable")
```

### 3.6 Rate Limiting & Costs

**Rate Limiting:**
- Limit AI calls per user per day (e.g., 50 requests)
- Admin users: unlimited
- Cache common responses (e.g., tag suggestions)

**Cost Management:**
- Set `max_tokens` limit (default: 1000)
- Use cheaper models where appropriate
- Implement request logging for cost tracking
- Add usage metrics to admin panel

### 3.7 Caching Strategy

**Cache AI Responses:**
- Tag suggestions for recipes (keyed by ingredients + title)
- Common search queries
- Cache duration: 24 hours
- Store in memory or Redis (future enhancement)

---

## 4. AIService Interface Design

### Core Methods

```python
class AIService:
    def __init__(self, api_key: str, org_id: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key, organization=org_id)
    
    async def call_llm(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generic LLM call with retry logic and error handling"""
        pass
    
    async def suggest_tags(self, recipe_title: str, ingredients: List[str]) -> List[str]:
        """Suggest tags for a recipe"""
        pass
    
    async def search_recipes(self, natural_query: str) -> dict:
        """Convert natural language to search parameters"""
        pass
    
    async def extract_recipe_from_text(self, text: str) -> dict:
        """Parse recipe from unstructured text"""
        pass
    
    async def calculate_nutrition(self, ingredients: List[dict]) -> dict:
        """Calculate nutrition facts"""
        pass
```

---

## 5. Admin AI Testing Interface (Story #1003)

### Features:
1. **Model Selection**: Dropdown to choose GPT model
2. **System Prompt**: Editable text area
3. **User Prompt**: Text input for testing
4. **Response Format**: JSON/Text toggle
5. **Execute Button**: Trigger LLM call
6. **Response Display**: Formatted output
7. **Token Usage**: Show tokens used and estimated cost
8. **History**: Last 10 test calls

### UI Design:
```
┌─────────────────────────────────────────────┐
│ AI Testing Interface                        │
├─────────────────────────────────────────────┤
│ Model: [gpt-4o-mini ▼]  Temperature: [0.7] │
│                                             │
│ System Prompt:                              │
│ ┌─────────────────────────────────────────┐ │
│ │ You are a helpful assistant...          │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ User Prompt:                                │
│ ┌─────────────────────────────────────────┐ │
│ │ Suggest tags for: Spaghetti Carbonara   │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Format: [○ Text ● JSON]                    │
│                                             │
│ [🚀 Execute]                                │
│                                             │
│ Response:                                   │
│ ┌─────────────────────────────────────────┐ │
│ │ {                                       │ │
│ │   "tags": ["Italian", "Pasta", ...]    │ │
│ │ }                                       │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Tokens: 245 | Cost: $0.0012                │
└─────────────────────────────────────────────┘
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Story #1002)
1. Add OpenAI dependency
2. Create `AIService` class
3. Add environment configuration
4. Implement basic `call_llm()` method
5. Add unit tests

### Phase 2: Admin Interface (Story #1003)
1. Create `/admins/ai/test` endpoint
2. Add frontend admin tab for AI testing
3. Implement model selection
4. Add prompt editing
5. Display responses and usage

### Phase 3: Tag Suggestions (Story #1004)
1. Implement tag suggestion prompt
2. Create `/recipes/{id}/suggest-tags` endpoint
3. Add frontend UI button
4. Cache responses

### Phase 4: AI Search (Story #1005)
1. Implement natural language query parsing
2. Create `/recipes/ai-search` endpoint
3. Add frontend search bar enhancement
4. Integrate with existing search

### Phase 5: Recipe from Image (Story #1006)
1. Add OCR capability (OpenAI Vision or separate OCR)
2. Create recipe extraction prompt
3. Implement `/recipes/from-image` endpoint
4. Add frontend upload UI

### Phase 6: Nutrition Facts (Story #1007)
1. Implement nutrition calculation prompt
2. Add to recipe detail page
3. Cache nutrition data

---

## 7. Security Considerations

1. **API Key Protection**:
   - Never expose in logs
   - Rotate keys periodically
   - Use environment variables only

2. **Rate Limiting**:
   - Prevent API abuse
   - Protect from cost overruns

3. **Input Validation**:
   - Sanitize all prompts
   - Prevent prompt injection
   - Limit prompt length

4. **Admin-Only Access**:
   - AI testing interface restricted to superusers
   - Regular users: limited AI features only

---

## 8. Testing Strategy

1. **Unit Tests**:
   - Mock OpenAI responses
   - Test error handling
   - Validate response parsing

2. **Integration Tests**:
   - Test with real API (dev key)
   - Verify end-to-end flow
   - Test rate limiting

3. **Load Tests**:
   - Concurrent AI requests
   - Rate limit behavior
   - Cost monitoring

---

## 9. Monitoring & Observability

1. **Metrics**:
   - Total AI calls per day
   - Average response time
   - Token usage per endpoint
   - Cost per day

2. **Logging**:
   - Log all AI requests (prompts + responses)
   - Track errors and retries
   - Monitor API usage

3. **Alerts**:
   - Cost threshold exceeded
   - Error rate spike
   - API key issues

---

## 10. Cost Estimation

**Assumptions:**
- 100 active users
- 10 AI calls per user per day
- Average 500 tokens per call
- Model: gpt-4o-mini ($0.15/$1M input, $0.60/$1M output)

**Daily Cost:**
- 100 users × 10 calls = 1,000 calls/day
- 1,000 × 500 tokens = 500,000 tokens/day
- Input: ~$0.075/day
- Output: ~$0.30/day
- **Total: ~$0.38/day or $11.50/month**

**Cost Optimization:**
- Cache common responses: -30%
- Use gpt-3.5-turbo for simple tasks: -50%
- **Optimized: ~$5.75/month**

---

## Next Steps

1. ✅ Create this design document
2. ⏭️ Install OpenAI library
3. ⏭️ Implement AIService
4. ⏭️ Create admin testing interface
5. ⏭️ Implement tag suggestions
6. ⏭️ Add AI search capabilities

---

**Status**: Design Complete  
**Approval Required**: Yes (review cost implications)  
**Estimated Implementation Time**: 8-12 hours across 3 stories

