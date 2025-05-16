# implementation notes and questions

## General
- how move or rename the "app" folder to "backend"
- is .env used only by the backend or also by the frontend?
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