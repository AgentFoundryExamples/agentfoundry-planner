# File Summaries

Heuristic summaries of source files based on filenames, extensions, and paths.

Schema Version: 2.0

Total files: 10

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
**Size:** 6.28 KB  
**LOC:** 145  
**TODOs/FIXMEs:** 0  
**Declarations:** 6  
**Top-level declarations:**
  - async function lifespan
  - async function http_exception_handler
  - async function health_check
  - async function create_plan
  - function _verify_debug_auth
  - async function debug_context
**External Dependencies:**
  - **Stdlib:** `contextlib.asynccontextmanager`, `os`, `typing.AsyncGenerator`, `uuid.uuid4`
  - **Third-party:** `fastapi.FastAPI`, `fastapi.HTTPException`, `fastapi.Header`, `fastapi.Request`, `fastapi.responses.JSONResponse`

## planner_service/context_driver.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 4.84 KB  
**LOC:** 97  
**TODOs/FIXMEs:** 0  
**Declarations:** 3  
**Top-level declarations:**
  - class ContextDriver
  - class StubContextDriver
  - function get_context_driver
**External Dependencies:**
  - **Stdlib:** `importlib.resources`, `json`, `typing.Protocol`, `typing.runtime_checkable`
  - **Third-party:** `af_github_core.GitHubContextDriver`

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

## planner_service/prompt_engine.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 4.69 KB  
**LOC:** 87  
**TODOs/FIXMEs:** 0  
**Declarations:** 3  
**Top-level declarations:**
  - class PromptEngine
  - class StubPromptEngine
  - function get_prompt_engine
**External Dependencies:**
  - **Stdlib:** `typing.Protocol`, `typing.runtime_checkable`, `uuid.uuid4`
  - **Third-party:** `af_prompt_core.PromptEngineBackend`

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

## tests/test_context_driver.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 10.61 KB  
**LOC:** 196  
**TODOs/FIXMEs:** 0  
**Declarations:** 5  
**Top-level declarations:**
  - function client
  - class TestContextDriverProtocol
  - class TestStubContextDriver
  - class TestGetContextDriverFactory
  - class TestDebugContextEndpoint
**External Dependencies:**
  - **Stdlib:** `builtins`, `sys`, `unittest.mock.MagicMock`, `unittest.mock.patch`
  - **Third-party:** `fastapi.testclient.TestClient`, `pytest`

## tests/test_prompt_engine.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 10.19 KB  
**LOC:** 211  
**TODOs/FIXMEs:** 0  
**Declarations:** 5  
**Top-level declarations:**
  - function sample_planning_context
  - class TestPromptEngineProtocol
  - class TestStubPromptEngine
  - class TestGetPromptEngineFactory
  - class TestMultipleProjectContextHandling
**External Dependencies:**
  - **Stdlib:** `builtins`, `unittest.mock.MagicMock`, `unittest.mock.patch`
  - **Third-party:** `pytest`
