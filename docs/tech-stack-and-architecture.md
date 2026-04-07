# Tech Stack & Architecture

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | FastAPI | 0.123.4 |
| **ORM** | SQLModel (on SQLAlchemy) | 0.0.24 |
| **Database** | PostgreSQL | via psycopg2-binary |
| **Migrations** | Alembic | 1.17.2 |
| **Auth** | JWT (python-jose) + bcrypt (passlib) | — |
| **AI** | OpenAI SDK | 2.14.0 |
| **PDF Export** | ReportLab | 4.4.7 |
| **BaaS** | Supabase | 2.16.0 |
| **Settings** | pydantic-settings + `.env` | — |
| **Python** | 3.13+ (managed with uv) | — |
| **Frontend** | React + TypeScript | 19.1 / 5.8 |
| **Build** | Vite | 6.3 |
| **Styling** | Tailwind CSS + shadcn/ui (Radix + CVA) | 3.4 |
| **Routing** | react-router-dom | 7.6 |
| **i18n** | Custom React Context (EN + HE with RTL) | — |
| **Backend Tests** | pytest + pytest-asyncio + pytest-cov | 248 tests |
| **Frontend Tests** | Vitest + Testing Library + MSW | — |

## Architecture Highlights

**Monorepo layout** — `backend/` and `frontend/` as sibling directories under one git repo, no root-level orchestration tooling.

**Data model** — Users own Recipes (via UUID FK). Tags attach to Recipes through a `recipe_tags` join table. LLM configs are stored separately with global/service-level scoping.

**AI features** — Tag suggestion, natural language search, and nutrition calculation, all powered by OpenAI with database-driven prompt templates and model settings configurable through an admin UI.

---

## Backend Architecture

### Directory Structure

```
backend/
├── src/
│   ├── main.py                    # FastAPI app, middleware, routers
│   ├── core/                      # config, security, supabase client
│   ├── models/                    # SQLModel DB models + Pydantic schemas
│   ├── services/                  # Business logic layer
│   ├── api/v1/endpoints/          # Route handlers
│   └── utils/                     # DB session, dependencies
├── migrations/versions/           # 13 Alembic revisions
├── scripts/                       # DB backup/restore, tag population
└── tests/                         # Mirrors src/ (api, models, services)
```

### Layered Design

Classic `endpoints` → `services` → `models` separation. Endpoints handle HTTP concerns (request parsing, response formatting, auth checks). Services contain all business logic and database operations. Models define both database tables (SQLModel) and API schemas (Pydantic).

### Database Models

| Model | Table | Key Fields |
|-------|-------|------------|
| **User** | `users` | email, hashed_password, full_name, is_active, is_superuser, uuid |
| **Recipe** | `recipes` | title, description, ingredients (JSON), instructions (JSON), prep/cook time, servings, difficulty, user_id → users.uuid |
| **Tag** | `tags` | name, category, recipe_counter |
| **RecipeTag** | `recipe_tags` | recipe_id → recipes.id, tag_id → tags.id (M2M join) |
| **LLMConfig** | `llm_configs` | config_type, service_name, provider, model, temperature, max_tokens, prompts, is_active |

### Services

| Service | Responsibility |
|---------|---------------|
| **UserService** | CRUD, login/JWT, user search, delete with recipe transfer |
| **RecipeService** | CRUD with tag integration, public/my/admin lists, PDF/JSON export |
| **TagService** | Tag CRUD, search, popular/grouped, recipe-tag associations |
| **AIService** | OpenAI calls for tag suggestions, NL search, nutrition calculation |
| **LLMConfigService** | LLM config CRUD, 4-level cascade (Runtime > Service DB > Global DB > Env) |

### API Endpoints (all under `/api/v1`)

| Group | Routes | Auth |
|-------|--------|------|
| **Users** | register, login, CRUD, search, set-superuser | Mixed (some public, some need auth) |
| **Recipes** | list, my, detail, create, update, delete, export PDF/JSON | Mixed (list/detail public, mutations need auth, JSON export needs admin) |
| **Tags** | list, search, popular, grouped, recipe tags | Mostly public |
| **Admin** | config-test, test-setup, test-db, all recipes, tag CRUD | Admin-intended |
| **AI** | test, suggest-tags, search, nutrition | Needs OpenAI key configured |
| **LLM Configs** | CRUD, global, service, effective | Bearer + superuser enforced |

### Auth System

- **Passwords**: bcrypt via passlib
- **JWT**: python-jose with HS256, claims include `sub` (email), `user_id`, `uuid`, `is_superuser`
- **Middleware**: Intercepts requests, decodes JWT from `Authorization: Bearer`, sets `request.state.user`; public routes are whitelisted to skip auth
- **OAuth2 dependency**: `OAuth2PasswordBearer` + `get_current_user` used explicitly in LLM config routes

### Database Setup

- **Engine**: SQLAlchemy `create_engine` with `pool_pre_ping=True`, `pool_recycle=300`
- **Sessions**: `get_db` yields `SQLModelSession(engine)` via context manager
- **Config**: `pydantic-settings.BaseSettings` loads from `.env` (DATABASE_URL, JWT secrets, OpenAI keys, Supabase credentials)

---

## Frontend Architecture

### Directory Structure

```
frontend/src/
├── main.tsx                       # Entry point, routes, providers
├── config.ts                      # API_URL = '/api/v1'
├── contexts/                      # AuthContext/Provider, LanguageContext
├── i18n/translations.ts           # EN + HE translation maps
├── hooks/useRecipeDeletion.ts     # Delete flow hook
├── lib/
│   ├── api-client.ts              # Singleton HTTP client (fetch-based)
│   └── utils.ts                   # cn() helper
├── components/
│   ├── layout/                    # MainLayout, PageContainer
│   ├── ui/                        # shadcn primitives (button, card, input, etc.)
│   ├── RecipeCard.tsx
│   ├── nutrition-modal.tsx
│   ├── LanguageSwitcher.tsx
│   └── ErrorBoundary.tsx
└── pages/                         # All route-level screens
```

### Routes

| Path | Page | Purpose |
|------|------|---------|
| `/` | HomePage | Landing page |
| `/about` | AboutPage | About |
| `/recipes` | RecipeListPage | Public recipe list |
| `/recipes/new` | RecipeCreatePage | Create recipe (with AI tag suggestions) |
| `/recipes/:id` | RecipeDetailPage | Detail view (export, nutrition) |
| `/recipes/:id/edit` | RecipeEditPage | Edit recipe |
| `/recipes/my` | MyRecipesPage | Current user's recipes |
| `/admin` | AdminPage | User/tag/recipe mgmt, LLM config |
| `/login` | LoginPage | Login |
| `/register` | RegisterPage | Registration |

### Components

- **Layout**: `MainLayout` — nav bar with auth-aware links, admin link for superusers, language switcher. `PageContainer` — titled page wrapper.
- **Domain**: `RecipeCard` — recipe summary with actions. `nutrition-modal` — AI nutrition facts display. `tag-selector` — tag picker with optional AI suggestions.
- **UI (shadcn/Radix)**: `button`, `card`, `input`, `label`, `select`, `textarea`, `confirmation-modal` — consistent primitives styled with Tailwind + CVA.
- **Infrastructure**: `ErrorBoundary` — class component for catching render errors.

### State Management

- **No** Redux, Zustand, or React Query — uses React Context + local `useState`/`useEffect`
- **AuthContext**: JWT stored in localStorage, decoded on mount with `jwt-decode`, provides `user`, `login`, `logout`
- **LanguageContext**: In-memory language toggle (EN/HE), sets `dir="rtl"` for Hebrew

### API Client

Singleton `apiClient` class using `fetch`. Attaches `Authorization: Bearer <token>` from localStorage. Covers all backend endpoints: auth, recipes, tags, admin, AI, and LLM config. Errors parsed as `ApiError` from JSON response `detail`.

### Dev Connectivity

- Vite dev server (port 5173) proxies `/api` → `http://localhost:8000` (FastAPI)
- Backend CORS allows `localhost:5173` and `127.0.0.1:5173`

---

## Testing

| Area | Runner | Scope |
|------|--------|-------|
| **Backend** | pytest (248 tests) | Models (validators, defaults), services (CRUD, business logic), API endpoints (auth, recipes, users) |
| **Frontend** | Vitest + Testing Library | Pages (login, register, recipe CRUD), components (RecipeCard, TagSelector, UI primitives), API client, auth context |
