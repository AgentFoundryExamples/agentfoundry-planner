# Dependency Graph

Intra-repository dependency analysis for Python and JavaScript/TypeScript files.

Includes classification of external dependencies as stdlib vs third-party.

## Statistics

- **Total files**: 6
- **Intra-repo dependencies**: 6
- **External stdlib dependencies**: 8
- **External third-party dependencies**: 9

## External Dependencies

### Standard Library / Core Modules

Total: 8 unique modules

- `contextlib.asynccontextmanager`
- `logging`
- `os`
- `sys`
- `typing.AsyncGenerator`
- `typing.Optional`
- `uuid.UUID`
- `uuid.uuid4`

### Third-Party Packages

Total: 9 unique packages

- `fastapi.FastAPI`
- `fastapi.HTTPException`
- `fastapi.Request`
- `fastapi.responses.JSONResponse`
- `fastapi.testclient.TestClient`
- `pydantic.BaseModel`
- `pydantic.Field`
- `pytest`
- `structlog`

## Most Depended Upon Files (Intra-Repo)

- `planner_service/logging.py` (2 dependents)
- `planner_service/models.py` (2 dependents)
- `planner_service/__init__.py` (1 dependents)
- `planner_service/api.py` (1 dependents)

## Files with Most Dependencies (Intra-Repo)

- `planner_service/api.py` (3 dependencies)
- `tests/test_app.py` (3 dependencies)
