# useful commands

- run the backend server from cursor-recipes/backend
    - uv run uvicorn src.main:app --reload --port 8000
- run the frontend from cursor-recipes/frontend
    - npm run dev
- run the backend tests with coverage from curesor-recipes:
    - uv run --directory backend pytest --cov=src --cov-report=term-missing

    - (cd backend && uv run pytest --cov=src --cov-report=term-missing)
- run the frontend tests with coverage from curesor-recipes:
    - npm run test:coverage --prefix frontend