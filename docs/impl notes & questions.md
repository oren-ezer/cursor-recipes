# implementation notes and questions

## How to
- run the frontend
    - cd to /Users/orenezer/my-data/repos/cursor/cursor-recipes/frontend
    - run "npm run dev"
- debug the frontend
    - run the npm server from within the IDE
- run the backend
    - cd to /Users/orenezer/my-data/repos/cursor/cursor-recipes/backend
    - run "uv run uvicorn src.main:app --reload"
- debug the backend
    - run the FastAPI server from within the IDE
- run the backend tests
    - "uv run pytest tests/ -v"
    - or previous version "python -m pytest tests/ -v"
- run the local supabase
    - cd to /Users/orenezer/my-data/repos/cursor/cursor-recipes/local-supabase/supabase
    - run "npx supabase start"

- run frontend tests:
    - Run all tests 'npm run test:run'
    - Run tests with UI 'npm run test:ui'
    - Run a specific test file 'npm run test:run tests/pages/RecipeEditPage.test.tsx'
    - Run a specific test suite 'npm run test:run tests/pages/RecipeCreatePage.test.tsx -- --reporter=verbose -t "Form Rendering"'
    - Run a specific test 'npm run test:run tests/pages/RecipeCreatePage.test.tsx -- --reporter=verbose -t "should render all form fields"'
    - Run tests with coverage 'npm run test:coverage'
    - Watch mode for development 'npm run test:watch'

    
## General
- how move or rename the "app" folder to "backend"
    - create src with all without scripts and tests. 
    - move conftest to inside test (or remove completely)
- is .env used only by the backend or also by the frontend?
    - for both
- do I need to know anything about what's in 'venv' folder?

- what is the best practice for import statements - begining? when needed/used? mixture? (see imports in main.py)

## Backend 
- do I need to know anything about what's in 'cursor_recipes.egg-info' metadata folder?
- why requirements.txt, setup.py, pytestdebug.log, conftest.py, alembic.ini, .env are in the workspace root and not in the backend root (currently named "app")
- why requirements.txt include more packages than setup.py
- what is the app/__init__.py empty file?
- how come the "schemas" dir is empty and why do i need it?
- where is the fucking logging?

### app
- refactor to 'backend'
- in main.py - why the exception handler are with @ and the middleware is not?
- in main.py - why the general exception handler has logging and the rest do not?
- in main.py - what is the purpose of the root() function? the "message" is actually coming from main.tsx
- in main.py - what is causeing the lifespan method to be called? is it the asynccontextmanager annotation?
- in main.py - why all the models and endpoints are being called on startup? is that for creating the runtime routing?

### endpoints
- why async def search_users(....) in users.py is being traversed twice during startuo while other methods do not?
- explain the request.app.state.supabase syntax and where app is coming from (originally it is named app_instance in main.py) and how it is populated on the request object
- with users count response - what is the best practice for implementing select count(*) with supabase client API
- can't we wrap all endpoint methods with an exception handler wrapper instead of the boiler plate exception handling code in each endpoint method impl?
- in users.py and the delete user endpoint - why commented code was left in the source?
- the async def read_users_me(request: Request): endpoint its purpose and its impl
- why all endpoints are async? is that a good practice?
- in users.py with login_for_access_token - why defaulting the is_active to True???
- the DB utils impl for recipes.py vs the supabase api impl for users.py
- isn't it common practice to cgeck for exactly 1 result when selecting by ID?
- users/me and recipes/me endpoints are failing very ugly from swagger. how to debug and fix it?
- how the user register is working with a password the does not include special chars but the update user swagger fails on it?

### core
- why the call to logging.basicConfig(level=logging.INFO) is done from within supabase_client.py and commented out in config.py?

### models
- in base.py - BaseModel and the deprecated datetime.utcnow (+ many other places in the code that was generate are using this)
- in base.py - BaseModel has the id as Optional. Why?
- isn't it better that BaseModel will hold the uuid field? the change is just moving it there?
- in recipe.py - what is the __table_args__ ?

### migrations
- can I exclude a table in the DB from the upgrade/downgrade migration process of Alembic?

### tests
- why not all test are implemented by cursor
- what is the best practice in python and can I impl unit + integration backend tests with the same package


## Frontend 
- relative paths instead of aliases in tsx files

## Local Supabase
- Started supabase local development setup.
    - API URL: http://127.0.0.1:54321
    - GraphQL URL: http://127.0.0.1:54321/graphql/v1
    - S3 Storage URL: http://127.0.0.1:54321/storage/v1/s3
    - DB URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
    - Studio URL: http://127.0.0.1:54323
    - Inbucket URL: http://127.0.0.1:54324
    - JWT secret:      super-secret-jwt-token-with-at-least-32-characters-long
    - anon key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
    - service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
    - S3 Access Key: 625729a08b95bf1b7ff351a663f3a23c
    - S3 Secret Key: 850181e4652dd023b7a98c58ae0d2d34bd487ee0cc3254aed6eda37307425907
    - S3 Region: local