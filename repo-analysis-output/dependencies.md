# Dependency Graph

Intra-repository dependency analysis for Python and JavaScript/TypeScript files.

Includes classification of external dependencies as stdlib vs third-party.

## Statistics

- **Total files**: 12
- **Intra-repo dependencies**: 23
- **External stdlib dependencies**: 15
- **External third-party dependencies**: 14

## External Dependencies

### Standard Library / Core Modules

Total: 15 unique modules

- `builtins`
- `contextlib.asynccontextmanager`
- `importlib.resources`
- `json`
- `logging`
- `os`
- `sys`
- `typing.AsyncGenerator`
- `typing.Optional`
- `typing.Protocol`
- `typing.runtime_checkable`
- `unittest.mock.MagicMock`
- `unittest.mock.patch`
- `uuid.UUID`
- `uuid.uuid4`

### Third-Party Packages

Total: 14 unique packages

- `af_github_core.GitHubContextDriver`
- `af_prompt_core.PromptEngineBackend`
- `fastapi.Depends`
- `fastapi.FastAPI`
- `fastapi.HTTPException`
- `fastapi.Header`
- `fastapi.Request`
- `fastapi.exceptions.RequestValidationError`
- `fastapi.responses.JSONResponse`
- `fastapi.testclient.TestClient`
- `pydantic.BaseModel`
- `pydantic.Field`
- `pytest`
- `structlog`

## Most Depended Upon Files (Intra-Repo)

- `planner_service/models.py` (6 dependents)
- `planner_service/logging.py` (5 dependents)
- `planner_service/context_driver.py` (3 dependents)
- `planner_service/prompt_engine.py` (3 dependents)
- `planner_service/api.py` (3 dependents)
- `planner_service/auth.py` (2 dependents)
- `planner_service/__init__.py` (1 dependents)

## Files with Most Dependencies (Intra-Repo)

- `planner_service/api.py` (6 dependencies)
- `tests/test_plan_endpoint.py` (4 dependencies)
- `tests/test_app.py` (3 dependencies)
- `tests/test_context_driver.py` (3 dependencies)
- `planner_service/context_driver.py` (2 dependencies)
- `planner_service/prompt_engine.py` (2 dependencies)
- `tests/test_prompt_engine.py` (2 dependencies)
- `planner_service/auth.py` (1 dependencies)
