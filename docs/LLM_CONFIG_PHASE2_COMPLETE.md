# Phase 2 Complete: LLM Configuration Service & AIService Integration

## ✅ What Was Implemented

### 1. LLMConfigService (`backend/src/services/llm_config_service.py`)

Created comprehensive configuration management service with:

**Core Methods:**
- `get_global_config()` - Get system-wide default configuration
- `get_service_config(service_name)` - Get service-specific configuration
- `get_effective_config(service_name, override_params)` - **Cascade resolution with fallback hierarchy**
- `get_config_by_id()`, `get_config_by_uuid()` - Configuration lookup
- `get_all_configs()`, `get_active_configs()` - List configurations

**CRUD Operations:**
- `create_config(admin_uuid, config_data)` - Create new configuration
- `update_config(config_id, update_data)` - Update existing configuration
- `delete_config(config_id)` - Soft delete (deactivate)
- `activate_config(config_id)` - Reactivate configuration

**Helper Methods:**
- `_config_to_dict(config)` - Convert model to dictionary
- `_get_env_defaults()` - Fallback to environment variables

### 2. Configuration Fallback Hierarchy ⭐

Implemented **4-level cascade** with proper priority:

```
Priority (Highest → Lowest):
1. Runtime Overrides  ← Temporary per-call parameters
2. Service Config     ← Database service-specific settings  
3. Global Config      ← Database system-wide defaults
4. Environment Vars   ← Hardcoded fallback (settings.py)
```

**Logic Flow:**
```python
config = get_global_config()       # Start with level 3
   ↓
if service_config_exists:
    config.update(service_config)  # Override with level 2
   ↓
if runtime_overrides:
    config.update(runtime_params)  # Override with level 1
   ↓
return effective_config            # Result: Cascaded configuration
```

**Special Handling:**
- ✅ `None` values don't override existing settings
- ✅ Only non-`None` values from higher priority levels override lower levels
- ✅ Graceful degradation if database configs don't exist

### 3. Updated AIService (`backend/src/services/ai_service.py`)

**Constructor Changes:**
```python
# Before:
def __init__(self, api_key, org_id, default_model, default_temperature, default_max_tokens):
    # Hardcoded defaults

# After:
def __init__(self, db: Session, api_key, org_id):
    self.config_service = LLMConfigService(db)
    # Database-driven configuration
```

**Enhanced `call_llm()` Method:**
- Added `service_name` parameter for config lookup
- Implements configuration cascade automatically
- Logs effective configuration for debugging
- All parameters become runtime overrides

**Updated Service Methods:**
All AI service methods now support configuration:

1. **`suggest_tags()`**
   - Uses `"tag_suggestion"` service config
   - Supports template-based prompts with `{placeholders}`
   - Accepts `config_override` parameter
   
2. **`parse_natural_language_search()`**
   - Uses `"natural_language_search"` service config
   - Simplified with config delegation
   
3. **`calculate_nutrition()`**
   - Uses `"nutrition_calculation"` service config
   - Consistent override pattern

### 4. Comprehensive Tests (`backend/tests/services/test_llm_config_service.py`)

Created 6 tests verifying the fallback hierarchy:

- ✅ `test_get_effective_config_with_global_only` - Global fallback
- ✅ `test_get_effective_config_with_service_override` - Service overrides global
- ✅ `test_get_effective_config_with_runtime_override` - Runtime has highest priority
- ✅ `test_get_effective_config_cascade_hierarchy` - Complete cascade flow
- ✅ `test_config_to_dict_conversion` - Model to dict conversion
- ✅ `test_none_values_not_override` - None handling

**Test Results:** All 6 tests passing ✅

## 📊 Configuration Examples

### Example 1: Service with No Specific Config
```python
# Database:
# - Global config: gpt-4o-mini, temp=0.7, max_tokens=1000
# - No service config for "new_feature"

config = llm_config_service.get_effective_config("new_feature")
# Result:
# {
#   "model": "gpt-4o-mini",      ← From global
#   "temperature": 0.7,           ← From global
#   "max_tokens": 1000,           ← From global
#   "system_prompt": "Global..."  ← From global
# }
```

### Example 2: Service with Specific Config
```python
# Database:
# - Global config: gpt-4o-mini, temp=0.7, max_tokens=1000
# - Service config for "tag_suggestion": gpt-4o, temp=0.5, max_tokens=500

config = llm_config_service.get_effective_config("tag_suggestion")
# Result:
# {
#   "model": "gpt-4o",            ← From service (overrides global)
#   "temperature": 0.5,           ← From service (overrides global)
#   "max_tokens": 500,            ← From service (overrides global)
#   "system_prompt": "Tag..."     ← From service
# }
```

### Example 3: Runtime Override
```python
# Database:
# - Service config for "nutrition": gpt-4o, temp=0.3, max_tokens=500

config = llm_config_service.get_effective_config(
    "nutrition",
    override_params={"temperature": 0.9, "model": "gpt-4o-mini"}
)
# Result:
# {
#   "model": "gpt-4o-mini",       ← From runtime (overrides service)
#   "temperature": 0.9,           ← From runtime (overrides service)
#   "max_tokens": 500,            ← From service (not overridden)
# }
```

## 🔄 How AI Calls Now Work

### Before (Phase 1):
```python
ai_service = AIService(api_key="...", default_model="gpt-4o-mini")
tags = await ai_service.suggest_tags(title, ingredients)
# Always used hardcoded defaults
```

### After (Phase 2):
```python
ai_service = AIService(db=session, api_key="...")
tags = await ai_service.suggest_tags(title, ingredients)
# Automatically resolves configuration:
# 1. Check: Service config for "tag_suggestion"
# 2. Fallback: Global config
# 3. Final fallback: Environment variables
```

### With Runtime Override:
```python
tags = await ai_service.suggest_tags(
    title, 
    ingredients,
    config_override={"temperature": 0.8, "model": "gpt-4o"}
)
# Runtime params take precedence over database config
```

## 📁 Files Created/Modified

### Created:
- ✅ `backend/src/services/llm_config_service.py`
- ✅ `backend/tests/services/test_llm_config_service.py`

### Modified:
- ✅ `backend/src/services/ai_service.py` - Complete refactor for config support

## 🧪 Testing

- **LLMConfigService Tests**: 6/6 passing ✅
- **Fallback Hierarchy**: Fully tested ✅
- **Cascade Logic**: Verified with multiple scenarios ✅

## 🎯 Key Benefits

1. **Flexibility**: Admins can tune LLM settings without code changes
2. **Granular Control**: Different settings for different AI services
3. **Testing**: Runtime overrides enable A/B testing and experimentation
4. **Cost Optimization**: Use cheaper models for less critical services
5. **Performance Tuning**: Adjust temperature/tokens per service needs
6. **Graceful Degradation**: Falls back through multiple levels if configs missing
7. **Backward Compatible**: Existing code works with minimal changes

## 🚦 Configuration Resolution Flow

```
AI Service Call
      ↓
service_name="tag_suggestion"
      ↓
LLMConfigService.get_effective_config()
      ↓
┌─────────────────────────────────────┐
│ 1. Get Global Config from DB        │ ← "Default global LLM configuration"
│    model: gpt-4o-mini               │
│    temperature: 0.7                 │
│    max_tokens: 1000                 │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│ 2. Get Service Config from DB       │ ← Service-specific entry
│    service_name="tag_suggestion"    │
│    model: gpt-4o (overrides)        │
│    temperature: 0.5 (overrides)     │
│    max_tokens: 500 (overrides)      │
└─────────────────────────────────────┘
      ↓
┌─────────────────────────────────────┐
│ 3. Apply Runtime Overrides          │ ← Function call params
│    temperature: 0.9 (overrides)     │
└─────────────────────────────────────┘
      ↓
Final Effective Config:
{
  "model": "gpt-4o",           ← From service
  "temperature": 0.9,          ← From runtime (highest priority)
  "max_tokens": 500,           ← From service
  "system_prompt": "...",      ← From service
  "response_format": "json"    ← From service
}
      ↓
Make OpenAI API Call
```

## ⚠️ Important Notes

### Seed Data is Active!
The migration created:
1. **Global config** - Used as fallback for all services without specific config
2. **Tag suggestion config** - Used automatically by `suggest_tags()` method

### Breaking Change in AIService Constructor
```python
# Old (won't work anymore):
AIService(api_key="...", default_model="...")

# New (required):
AIService(db=session, api_key="...")
```

### Service Names
Standard service names (used in config lookups):
- `"tag_suggestion"` - Recipe tag suggestions
- `"natural_language_search"` - Search query parsing
- `"nutrition_calculation"` - Nutrition estimation
- `"general"` - Default/generic LLM calls

---

**Phase 2 Status: ✅ COMPLETE**

**Next Steps:** Phase 3 - API Endpoints for admin configuration management


