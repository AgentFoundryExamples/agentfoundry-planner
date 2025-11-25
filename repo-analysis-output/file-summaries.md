# File Summaries

Heuristic summaries of source files based on filenames, extensions, and paths.

Schema Version: 2.0

Total files: 6

## planner_service/__init__.py
**Language:** Python  
**Role:** module-init  
**Role Justification:** module initialization file '__init__'  
**Size:** 0.98 KB  
**LOC:** 2  
**TODOs/FIXMEs:** 0  

## planner_service/api.py
**Language:** Python  
**Role:** api  
**Role Justification:** filename contains 'api'  
**Size:** 3.80 KB  
**LOC:** 82  
**TODOs/FIXMEs:** 0  
**Declarations:** 4  
**Top-level declarations:**
  - async function lifespan
  - async function http_exception_handler
  - async function health_check
  - async function create_plan
**External Dependencies:**
  - **Stdlib:** `contextlib.asynccontextmanager`, `typing.AsyncGenerator`, `uuid.uuid4`
  - **Third-party:** `fastapi.FastAPI`, `fastapi.HTTPException`, `fastapi.Request`, `fastapi.responses.JSONResponse`

## planner_service/logging.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 3.12 KB  
**LOC:** 57  
**TODOs/FIXMEs:** 0  
**Declarations:** 3  
**Top-level declarations:**
  - function get_log_level
  - function configure_logging
  - function get_logger
**External Dependencies:**
  - **Stdlib:** `logging`, `os`, `sys`
  - **Third-party:** `structlog`

## planner_service/models.py
**Language:** Python  
**Role:** model  
**Role Justification:** model/schema name 'models'  
**Size:** 4.22 KB  
**LOC:** 81  
**TODOs/FIXMEs:** 0  
**Declarations:** 10  
**Top-level declarations:**
  - class RepositoryPointer
  - class UserInput
  - class ProjectContext
  - class PlanningContext
  - class PlanRequest
  - class PlanStep
  - class PlanResponse
  - class ErrorDetail
  - class ErrorResponse
  - class HealthResponse
**External Dependencies:**
  - **Stdlib:** `typing.Optional`, `uuid.UUID`
  - **Third-party:** `pydantic.BaseModel`, `pydantic.Field`

## tests/__init__.py
**Language:** Python  
**Role:** test  
**Role Justification:** located in 'tests' directory  
**Size:** 0.92 KB  
**LOC:** 1  
**TODOs/FIXMEs:** 0  

## tests/test_app.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 6.97 KB  
**LOC:** 154  
**TODOs/FIXMEs:** 0  
**Declarations:** 6  
**Top-level declarations:**
  - function client
  - class TestHealthEndpoint
  - class TestPlanEndpoint
  - class TestModels
  - class TestAppInitialization
  - class TestLogging
**External Dependencies:**
  - **Stdlib:** `uuid.UUID`, `uuid.uuid4`
  - **Third-party:** `fastapi.testclient.TestClient`, `pytest`
