# File Summaries

Heuristic summaries of source files based on filenames, extensions, and paths.

Schema Version: 2.0

Total files: 12

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
**Size:** 12.31 KB  
**LOC:** 297  
**TODOs/FIXMEs:** 0  
**Declarations:** 8  
**Top-level declarations:**
  - async function lifespan
  - async function http_exception_handler
  - async function validation_exception_handler
  - async function health_check
  - async function healthz
  - async function create_plan
  - function _verify_debug_auth
  - async function debug_context
**External Dependencies:**
  - **Stdlib:** `contextlib.asynccontextmanager`, `os`, `typing.AsyncGenerator`, `uuid.UUID`, `uuid.uuid4`
  - **Third-party:** `fastapi.Depends`, `fastapi.FastAPI`, `fastapi.HTTPException`, `fastapi.Header`, `fastapi.Request`
    _(and 2 more)_

## planner_service/auth.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 2.71 KB  
**LOC:** 38  
**TODOs/FIXMEs:** 0  
**Declarations:** 2  
**Top-level declarations:**
  - class AuthContext
  - function get_current_user
**External Dependencies:**
  - **Stdlib:** `typing.Optional`
  - **Third-party:** `fastapi.Header`, `pydantic.BaseModel`, `pydantic.Field`

## planner_service/context_driver.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 5.04 KB  
**LOC:** 100  
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
**Size:** 8.00 KB  
**LOC:** 166  
**TODOs/FIXMEs:** 0  
**Declarations:** 12  
**Top-level declarations:**
  - function _validate_non_empty_string
  - function _validate_non_empty_strings
  - class RepositoryPointer
  - class UserInput
  - class ProjectContext
  - class PlanningContext
  - class PlanRequest
  - class PlanStep
  - class PlanResponse
  - class ErrorDetail
  - ... and 2 more
**External Dependencies:**
  - **Stdlib:** `typing.Optional`, `uuid.UUID`
  - **Third-party:** `pydantic.BaseModel`, `pydantic.ConfigDict`, `pydantic.Field`, `pydantic.StrictStr`, `pydantic.ValidationInfo`
    _(and 1 more)_

## planner_service/prompt_engine.py
**Language:** Python  
**Role:** implementation  
**Role Justification:** general implementation file (default classification)  
**Size:** 4.98 KB  
**LOC:** 90  
**TODOs/FIXMEs:** 0  
**Declarations:** 3  
**Top-level declarations:**
  - class PromptEngine
  - class StubPromptEngine
  - function get_prompt_engine
**External Dependencies:**
  - **Stdlib:** `typing.Protocol`, `typing.runtime_checkable`
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
**Size:** 7.47 KB  
**LOC:** 159  
**TODOs/FIXMEs:** 0  
**Declarations:** 7  
**Top-level declarations:**
  - function client
  - function _make_user_input
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
**Size:** 10.22 KB  
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

## tests/test_plan_endpoint.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 19.70 KB  
**LOC:** 422  
**TODOs/FIXMEs:** 0  
**Declarations:** 10  
**Top-level declarations:**
  - function client
  - function _make_user_input
  - class TestPlanEndpointAuth
  - class TestPlanEndpointHappyPath
  - class TestPlanEndpointContextDriverFailure
  - class TestPlanEndpointPromptEngineFailure
  - class TestPlanEndpointValidation
  - class TestHealthEndpoints
  - class TestAuthContextModel
  - class TestGetCurrentUserDependency
**External Dependencies:**
  - **Stdlib:** `unittest.mock.patch`, `uuid.UUID`
  - **Third-party:** `fastapi.testclient.TestClient`, `pytest`

## tests/test_prompt_engine.py
**Language:** Python  
**Role:** test  
**Role Justification:** filename starts with 'test_'  
**Size:** 10.30 KB  
**LOC:** 217  
**TODOs/FIXMEs:** 0  
**Declarations:** 5  
**Top-level declarations:**
  - function sample_planning_context
  - class TestPromptEngineProtocol
  - class TestStubPromptEngine
  - class TestGetPromptEngineFactory
  - class TestMultipleProjectContextHandling
**External Dependencies:**
  - **Stdlib:** `builtins`, `unittest.mock.MagicMock`, `unittest.mock.patch`, `uuid.uuid4`
  - **Third-party:** `pytest`
