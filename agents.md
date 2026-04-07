# AI Agent Instructions

## Project Overview

Full-stack recipe management app. Python backend + React frontend in a single git repo.

- **Backend**: `backend/` — FastAPI + SQLModel + PostgreSQL
- **Frontend**: `frontend/` — React 19 + TypeScript + Vite + Tailwind + shadcn/ui
- **Database**: PostgreSQL (via Supabase), migrations with Alembic
- **AI**: OpenAI SDK for tag suggestions, natural language search, nutrition calculation

## Running the Project

```bash
# Backend (from backend/)
uv run uvicorn src.main:app --reload --port 8000

# Frontend (from frontend/)
npm run dev          # Vite dev server on port 5173, proxies /api → localhost:8000

# Tests
uv run pytest        # Backend (from backend/)
npm run test:run     # Frontend (from frontend/)

# Build
npm run build        # Frontend (from frontend/) — runs tsc -b && vite build
```

## Backend Conventions

### Architecture

Layered design: `endpoints` → `services` → `models`. Never put business logic in endpoints. Never put HTTP concerns in services.

```
backend/src/
├── main.py                        # App, middleware, routers
├── core/config.py                 # pydantic-settings (Settings singleton)
├── core/security.py               # Password hashing, JWT creation
├── models/                        # SQLModel tables + Pydantic schemas
├── services/                      # Business logic, DB operations
├── api/v1/endpoints/              # Route handlers
└── utils/
    ├── database_session.py        # Engine, get_db()
    └── dependencies.py            # FastAPI DI (service factories, auth)
```

### Models

- All DB models extend `BaseModel` from `src/models/base.py` (provides `id`, `created_at`, `updated_at`).
- Use `SQLModel` with `table=True` for database tables.
- Use plain `Pydantic BaseModel` for request/response schemas (defined in endpoint files or `ai_models.py`).
- Use `datetime.now(timezone.utc)` for timestamps, never `datetime.utcnow()`.
- JSON columns (e.g., `ingredients`, `instructions`) store structured data as lists.

### Services

- Each service takes a `Session` in its constructor: `def __init__(self, db: Session)`.
- Services are instantiated via FastAPI dependency injection (see `dependencies.py`).
- The `AIService` additionally requires `LLMConfigService` in its constructor.
- Use hard deletes unless soft delete is explicitly required.

### Endpoints

- Routers use `APIRouter(prefix="/resource", tags=["resource"])`.
- All routers are mounted in `main.py` with `prefix=settings.API_V1_STR` (`/api/v1`).
- Use `Annotated[ServiceType, Depends(get_service)]` for dependency injection.
- Auth: middleware populates `request.state.user` (a dict, not a model instance). Check it in the endpoint when auth is required.
- For admin-only routes, check `request.state.user["is_superuser"]`.
- The LLM config endpoints use `OAuth2PasswordBearer` + `get_current_user` / `get_admin_user` as explicit dependencies — follow this pattern for new admin-protected routes.

### Database & Migrations

- Engine and session in `src/utils/database_session.py`.
- Use `get_db()` or `get_database_session()` as FastAPI dependencies — both yield a `SQLModelSession`.
- Alembic config in `backend/alembic.ini`, migrations in `backend/migrations/versions/`.
- `DATABASE_URL` comes from `.env` via pydantic-settings.
- When creating migrations, import new models in `migrations/env.py` for autogenerate to detect them.

### Configuration

- All config via `src/core/config.py` → `settings` singleton (pydantic-settings `BaseSettings`).
- Loads from `.env` file. Required: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`.
- Optional: `OPENAI_API_KEY`, `OPENAI_ORG_ID`, `SECRET_KEY`.
- Never hardcode secrets or connection strings.

### LLM / AI Configuration

- LLM settings are stored in the `llm_configs` DB table with a 4-level cascade: Runtime override > Service-specific DB config > Global DB config > Environment variable defaults.
- Prompt templates use single curly braces for placeholders: `{ingredients}`, `{recipe_title}`, `{existing_tags}`.
- When adding a new AI feature: create a migration to seed its LLM config, add a method to `AIService`, and use `self.config_service.get_effective_config("service_name")` to retrieve settings.
- Enum values for `LLMProvider` and `LLMConfigType` are UPPERCASE: `"OPENAI"`, `"GLOBAL"`, `"SERVICE"`.

### Testing

- pytest with `asyncio_mode = auto`.
- Tests mirror `src/` structure: `tests/models/`, `tests/services/`, `tests/api/v1/`.
- `conftest.py` provides a `client` fixture (`TestClient(app)`).
- Model tests validate field defaults, constraints, and validators without a live DB.
- Service tests mock database sessions.
- Run with: `uv run pytest` (from `backend/`).
- Fix all warnings — use `datetime.now(timezone.utc)`, `min_length` (not `min_items`), etc.

## Frontend Conventions

### Architecture

```
frontend/src/
├── main.tsx                       # Entry: providers + routes
├── config.ts                      # API_URL = '/api/v1'
├── contexts/                      # AuthContext, LanguageContext
├── i18n/translations.ts           # EN + HE translation maps
├── hooks/                         # Custom hooks
├── lib/
│   ├── api-client.ts              # Singleton ApiClient class
│   └── utils.ts                   # cn() (clsx + tailwind-merge)
├── components/
│   ├── layout/                    # MainLayout, PageContainer
│   ├── ui/                        # shadcn primitives
│   └── ...                        # Domain components
└── pages/                         # Route-level screens
```

### Components

- Use functional components with TypeScript.
- shadcn/ui primitives live in `components/ui/` — use Radix + CVA + `cn()` for variants.
- Layout components: `MainLayout` (nav + auth), `PageContainer` (titled wrapper).
- New components go in `components/` (domain) or `components/ui/` (generic primitives).
- `App.tsx` is unused boilerplate from Vite template — the real entry is `main.tsx`.

### State Management

- React Context only — no Redux, Zustand, or React Query.
- `AuthContext` / `AuthProvider`: JWT in localStorage, decoded with `jwt-decode`, provides `user`, `login`, `logout`, `isAuthenticated`, `isLoading`.
- `LanguageContext` / `LanguageProvider`: in-memory language toggle, sets `document.dir` for RTL.
- Page-level state uses `useState` / `useEffect`.

### API Client

- Singleton `apiClient` exported from `src/lib/api-client.ts`.
- Uses `fetch` with `Authorization: Bearer <token>` from localStorage.
- All API methods return typed responses.
- Errors thrown as `ApiError` (single argument: message string).
- When adding new endpoints: add a method to `ApiClient` class and export the corresponding TypeScript interface.

### Internationalization (i18n)

This is mandatory for all user-facing text. See `frontend/I18N_GUIDELINES.md` for full details.

- Use `const { t } = useLanguage()` in every component with user-facing text.
- Never hardcode strings in JSX — use `t('section.subsection.key')`.
- Add every new key to BOTH `en` and `he` in `src/i18n/translations.ts`.
- Use semantic, hierarchical key names: `recipe.form.title`, `admin.llm_config.provider`.
- The `TranslationKey` type is auto-derived from the `en` keys — TypeScript will catch missing keys at build time.
- Test both languages and verify RTL layout for Hebrew.

### Styling

- Tailwind CSS 3 with `darkMode: ['class']`.
- CSS variables for shadcn theming in `src/index.css`.
- Use `cn()` from `src/lib/utils.ts` for conditional class merging.
- Use Tailwind's `rtl:` modifier for directional styles: `ml-4 rtl:mr-4 rtl:ml-0`.

### Routing

- All routes defined in `main.tsx` using `react-router-dom` v7.
- Pages are standalone components in `src/pages/`.
- Admin UI is gated by `user.is_superuser` in the frontend — backend enforcement is separate.

### Testing

- Vitest + Testing Library (`@testing-library/react`) + jsdom.
- Tests in `frontend/tests/`, mirroring `src/` structure.
- Custom `render` wrapper in `tests/setup/test-utils.tsx` provides `LanguageProvider`, `BrowserRouter`, `AuthProvider`.
- MSW handlers defined but API client tests mock `global.fetch` directly.
- Run with: `npm run test:run` (from `frontend/`).

## Adding a New Feature (Checklist)

### Backend

1. Define the model in `src/models/` (extend `BaseModel` if it needs a DB table).
2. Create an Alembic migration: `uv run alembic revision --autogenerate -m "description"`.
3. Add a service in `src/services/` with constructor taking `Session`.
4. Register a DI factory in `src/utils/dependencies.py`.
5. Add endpoint(s) in `src/api/v1/endpoints/`.
6. Mount the router in `src/main.py`.
7. Write tests in `tests/` (model + service + optionally API).

### Frontend

1. Add API method + TypeScript interface to `src/lib/api-client.ts`.
2. Add translation keys to `src/i18n/translations.ts` (both `en` and `he`).
3. Create page in `src/pages/` or component in `src/components/`.
4. Add route in `main.tsx` if it's a new page.
5. Write tests in `tests/`.

### Pre-commit Checks

```bash
# Backend
uv run pytest                    # All tests pass, 0 warnings from our code

# Frontend
npm run build                    # TypeScript compiles cleanly
npm run test:run                 # All tests pass
```

## Common Pitfalls

- **Prompt placeholders**: Use single curly braces `{variable}` in LLM prompt templates, not double `{{variable}}`.
- **Enum casing**: `LLMProvider` and `LLMConfigType` values are UPPERCASE in both backend and frontend.
- **Auth user type**: `request.state.user` is a `Dict[str, Any]`, not a model instance. Access fields with `user["uuid"]`, not `user.uuid`.
- **API errors**: `ApiError` constructor takes a single string argument. Don't pass status code as a second arg.
- **Translation keys**: Must exist in both `en` and `he`. Missing keys cause TypeScript build errors (TS2345).
- **`.gitignore`**: Root `lib/` is scoped to `/lib/` (root only). Don't add unscoped patterns that could match `frontend/src/lib/`.
- **Datetime**: Always use `datetime.now(timezone.utc)`, never `datetime.utcnow()` (deprecated in Python 3.12+).
- **Pydantic**: Use `min_length` for list validation, not `min_items` (deprecated in Pydantic v2).
