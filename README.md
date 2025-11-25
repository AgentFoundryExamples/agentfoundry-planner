# Planner Service

FastAPI planner service for Agent Foundry. This service provides a planning API endpoint that accepts repository and user input context, returning planning operations with request and run tracking identifiers.

## Features

- FastAPI-based REST API with OpenAPI documentation
- Pydantic models for request/response validation
- Structured logging with structlog (service-tagged)
- Cloud Run ready with health check endpoint
- Environment-based configuration with safe defaults
- Extensible context driver architecture with stub implementation
- Extensible prompt engine architecture with stub implementation

## Project Structure

```
planner-service/
├── planner_service/
│   ├── __init__.py         # Package initialization and version
│   ├── api.py              # FastAPI application and endpoints
│   ├── auth.py             # Authentication context and dependency
│   ├── context_driver.py   # Context driver abstraction and factory
│   ├── logging.py          # Structlog configuration
│   ├── models.py           # Pydantic data models
│   ├── plan_validator.py   # Plan validator abstraction for validating prompt engine output
│   ├── prompt_engine.py    # Prompt engine abstraction and factory
│   └── resources/
│       └── mock_context.json  # Mock context fixtures
├── tests/
│   ├── test_app.py         # Unit and integration tests
│   ├── test_context_driver.py  # Context driver tests
│   ├── test_plan_endpoint.py   # Plan endpoint tests
│   ├── test_plan_validator.py  # Plan validator tests
│   └── test_prompt_engine.py   # Prompt engine tests
├── docs/
│   └── versioning.md       # Version metadata and release notes
├── Dockerfile              # Cloud Run deployment
├── Makefile                # Developer targets (install, lint, test, run)
├── pyproject.toml          # Project metadata and dependencies
└── README.md
```

## Installation

### Prerequisites

- Python 3.11+
- pip
- make (optional, for developer targets)

### Using Makefile (Recommended)

The Makefile provides convenient targets for common development tasks using a virtual environment:

```bash
# Show available targets
make help

# Install package dependencies (creates .venv)
make install

# Install with dev dependencies (for testing/linting)
make install-dev

# Run linting (requires ruff)
make lint

# Run tests
make test

# Start development server with auto-reload
make run

# Clean build artifacts and virtualenv
make clean
```

Note: The Makefile creates a `.venv` directory for the virtual environment. If the virtualenv already exists, install commands will use it without recreating.

### Manual Installation

```bash
# Install package with dependencies
pip install -e .

# Install with dev dependencies (for testing)
pip install -e ".[dev]"
```

## Running the Server

### Using Makefile

```bash
# Start development server with auto-reload (uses .venv)
make run
```

### Local Development (Manual)

```bash
# Run with uvicorn (development mode with auto-reload)
uvicorn planner_service.api:app --reload --host 0.0.0.0 --port 8080

# Or run with default settings
uvicorn planner_service.api:app
```

### Docker

```bash
# Build the image
docker build -t planner-service .

# Run the container
docker run -p 8080:8080 planner-service

# Run with custom environment variables
docker run -p 8080:8080 \
  -e LOG_LEVEL=DEBUG \
  -e DEBUG_AUTH_TOKEN=my-secret-token \
  planner-service

# Run with port mapping to different host port
docker run -p 3000:8080 planner-service
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server port (used by Cloud Run) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DEBUG_AUTH_TOKEN` | `debug-token-stub` | Token for debug endpoint authentication |

Missing environment variables fall back to safe defaults without crashing server startup.

## API Endpoints

### Health Check

```
GET /health
GET /healthz
```

Returns service health status. Both endpoints return identical responses and are available even when downstream stubs fail to initialize. The `/healthz` endpoint follows Kubernetes naming conventions.

**Response:**
```json
{
  "status": "healthy",
  "service": "planner-service",
  "version": "0.1.0"
}
```

### Create Plan

```
POST /v1/plan
```

Create a new planning request. This endpoint implements a validator-driven pipeline that treats prompt output as untrusted data.

**Pipeline Flow (AF v1.1):**

1. **Request ID Generation**: A `request_id` is generated (or echoed from client) at the start of the handler
2. **Context Fetching**: Repository context is fetched via the context driver
3. **PlanningContext Construction**: The `request_id`, user input, and project context are assembled
4. **Prompt Engine Invocation**: The planning context is passed to the prompt engine
5. **Validation**: The prompt engine output is validated via `PlanValidator.validate()` - all code paths must pass through validation
6. **Response Generation**: On success, `run_id` is generated and `PlanResponse(status="ok", payload=validated_payload)` is returned with HTTP 200

**Error Handling:**

- **PlanValidationFailure** (invalid prompt output): Returns HTTP 422 with `ErrorResponse` containing `request_id` and error metadata - no `run_id` is included
- **Context/Engine failures**: Return HTTP 500 with `ErrorResponse` containing `request_id` - no `run_id` is included
- **Request validation errors**: Return HTTP 422 with `ErrorResponse` containing `request_id` - no `run_id` is included

**Authentication:**

The endpoint accepts an optional `Authorization` header with a Bearer token. If the header is missing or invalid, a stub user is used (with a warning logged for future enforcement).

```
Authorization: Bearer <token>
```

**Request Body (AF v1.1):**
```json
{
  "repository": {
    "owner": "string",
    "name": "string",
    "ref": "string (default: refs/heads/main)"
  },
  "user_input": {
    "purpose": "string",
    "vision": "string",
    "must": ["string", ...],
    "dont": ["string", ...],
    "nice": ["string", ...]
  },
  "request_id": "uuid (optional)"
}
```

**Success Response (200):**
```json
{
  "request_id": "uuid",
  "run_id": "uuid",
  "status": "ok",
  "payload": {
    "request_id": "uuid",
    "repository": {
      "owner": "myorg",
      "name": "myrepo",
      "ref": "refs/heads/main"
    },
    "status": "success",
    "prompt_preview": "[STUB] Planning request for myorg/myrepo: ..."
  }
}
```

Note: In the synchronous flow, `run_id` mirrors `request_id`. The `status` is "ok" when the prompt engine succeeds and validation passes.

**Validation Error Response (422):**

When plan validation fails (prompt output doesn't meet structural requirements):
```json
{
  "error": {
    "code": "MISSING_REQUEST_ID",
    "message": "Payload missing required key: request_id"
  },
  "request_id": "uuid"
}
```

Note: Validation error responses (422) include `request_id` but omit `run_id` to indicate no run was created.

**Server Error Response (5xx):**
```json
{
  "error": {
    "code": "CONTEXT_DRIVER_ERROR",
    "message": "Failed to fetch repository context: ..."
  },
  "request_id": "uuid"
}
```

Note: Error responses include `request_id` but omit `run_id` to indicate no run was created.

**Example Request:**
```bash
curl -X POST http://localhost:8080/v1/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my-token" \
  -d '{
    "repository": {
      "owner": "myorg",
      "name": "myrepo",
      "ref": "refs/heads/main"
    },
    "user_input": {
      "purpose": "Add user authentication feature",
      "vision": "Secure login system with session management",
      "must": ["Implement login endpoint", "Implement logout endpoint"],
      "dont": ["Store passwords in plaintext"],
      "nice": ["Add remember me functionality"]
    }
  }'
```

### API Documentation

- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

### Debug Context (Optional)

```
POST /v1/debug/context
```

Debug endpoint to fetch repository context using the configured context driver. Protected by bearer token authentication.

**Headers:**
```
Authorization: Bearer <DEBUG_AUTH_TOKEN>
```

**Request Body (AF v1.1):**
```json
{
  "owner": "string",
  "name": "string",
  "ref": "string (default: refs/heads/main)"
}
```

**Response (AF v1.1):**
```json
{
  "repo_owner": "string",
  "repo_name": "string",
  "ref": "refs/heads/main",
  "tree_json": null,
  "dependency_json": null,
  "summary_json": null
}
```

## Context Driver Architecture

The planner service uses an extensible context driver architecture to fetch repository context. This allows for different implementations depending on the deployment environment.

### ContextDriver Protocol

The `ContextDriver` protocol defines the interface for context drivers:

```python
class ContextDriver(Protocol):
    def fetch_context(self, repo: RepositoryPointer) -> ProjectContext:
        """Fetch project context for the given repository."""
        ...
```

### Available Drivers

| Driver | Description |
|--------|-------------|
| `StubContextDriver` | Returns deterministic mock data from bundled fixtures |
| `af_github_core.GitHubContextDriver` | (Private) Real GitHub API integration |

### Driver Selection

The `get_context_driver()` factory function selects the appropriate driver:

1. Attempts to import `af_github_core.GitHubContextDriver`
2. Falls back to `StubContextDriver` on `ImportError`
3. Logs the selected driver for debugging

### Custom Driver Implementation

To implement a custom context driver:

1. Create a class implementing the `ContextDriver` protocol:

```python
from planner_service.context_driver import ContextDriver
from planner_service.models import ProjectContext, RepositoryPointer

class MyCustomDriver:
    def fetch_context(self, repo: RepositoryPointer) -> ProjectContext:
        # Your implementation here (AF v1.1 format)
        # JSON artifact strings should default to "{}" when empty
        return ProjectContext(
            repo_owner=repo.owner,
            repo_name=repo.name,
            ref=repo.ref,
            tree_json="{}",  # Default to "{}" not None for strict typing
            dependency_json="{}",
            summary_json="{}",
        )
```

2. To use as the default driver, create a package named `af_github_core` with a `GitHubContextDriver` class, or modify the factory function in `context_driver.py`.

### StubContextDriver Output

The `StubContextDriver` returns `ProjectContext` entries with:
- `repo_owner`, `repo_name`, `ref`: Repository coordinates from the input `RepositoryPointer`
- `tree_json`, `dependency_json`, `summary_json`: JSON strings defaulting to `"{}"` when empty (never `None`)

This ensures strict typing compliance when the context is used in `PlanningContext` construction and validator payloads.

### Mock Context Fixtures

The `StubContextDriver` loads mock data from `planner_service/resources/mock_context.json`. The fixture format is:

```json
{
  "default": {
    "tree_json": "{\"type\": \"tree\", \"entries\": []}",
    "dependency_json": "{\"dependencies\": []}",
    "summary_json": "{\"default_branch\": \"main\", \"languages\": []}"
  },
  "repositories": {
    "owner/repo": {
      "tree_json": "...",
      "dependency_json": "...",
      "summary_json": "..."
    }
  }
}
```

- `default`: Default context returned for unknown repositories (JSON strings default to `"{}"` if missing)
- `repositories`: Specific context for known repositories (keyed by `owner/name`)

To add custom mock data, edit the fixture file or provide repository-specific entries.

## Prompt Engine Architecture

The planner service uses an extensible prompt engine architecture to delegate plan generation to pluggable prompt logic. This allows for different implementations depending on the deployment environment.

### PromptEngine Protocol

The `PromptEngine` protocol defines the interface for prompt engines:

```python
class PromptEngine(Protocol):
    def run(self, ctx: PlanningContext) -> dict:
        """Generate plan output from the given planning context."""
        ...
```

### Available Engines

| Engine | Description |
|--------|-------------|
| `StubPromptEngine` | Returns deterministic payload without network or LLM calls |
| `af_prompt_core.PromptEngineBackend` | (Private) Real LLM integration |

### Engine Selection

The `get_prompt_engine()` factory function selects the appropriate engine:

1. Attempts to import `af_prompt_core.PromptEngineBackend`
2. Falls back to `StubPromptEngine` on `ImportError`
3. Logs the selected engine for debugging

### StubPromptEngine Output Schema

The stub engine returns a deterministic payload with the following structure:

```json
{
  "request_id": "uuid-string",
  "plan_version": "af/1.1-stub",
  "repository": {
    "owner": "string",
    "name": "string",
    "ref": "refs/heads/main"
  },
  "user_input": {
    "purpose": "string",
    "vision": "string",
    "must": ["string", ...],
    "dont": ["string", ...],
    "nice": ["string", ...]
  },
  "context": [
    {
      "repo_owner": "string",
      "repo_name": "string",
      "ref": "refs/heads/main",
      "tree_json": "{}",
      "dependency_json": "{}",
      "summary_json": "{}"
    }
  ],
  "status": "success",
  "prompt_preview": "[STUB] Planning request for owner/name: purpose text..."
}
```

- `request_id`: The request ID from PlanningContext (matches top-level response ID)
- `plan_version`: Version of the plan output schema (uses `af/1.1-stub` for stub engine)
- `repository`: Repository metadata from the first project context (uses AF v1.1 field names)
- `user_input`: Mirrored user input data from PlanningContext for validator inspection
- `context`: Mirrored project contexts list with repository coordinates and JSON artifact strings
- `status`: Always "success" for stub (real engines may return "failure")
- `prompt_preview`: Stub preview showing `{repo_owner}/{repo_name}: {purpose}` (does not expose real prompts)

### Custom Engine Implementation

To implement a custom prompt engine:

1. Create a class implementing the `PromptEngine` protocol:

```python
from planner_service.prompt_engine import PromptEngine
from planner_service.models import PlanningContext

class MyCustomEngine:
    def run(self, ctx: PlanningContext) -> dict:
        # Extract repository from the first project context (AF v1.1)
        project = ctx.projects[0] if ctx.projects else None
        repo_owner = project.repo_owner if project else ""
        repo_name = project.repo_name if project else ""
        repo_ref = project.ref if project else "refs/heads/main"
        
        # Your implementation here (may call LLM, rules engine, etc.)
        # Must include request_id and plan_version for validator
        return {
            "request_id": str(ctx.request_id),
            "plan_version": "af/1.1-custom",  # Use your version identifier
            "repository": {
                "owner": repo_owner,
                "name": repo_name,
                "ref": repo_ref,
            },
            "user_input": {  # Mirror user_input for validator inspection
                "purpose": ctx.user_input.purpose,
                "vision": ctx.user_input.vision,
                "must": list(ctx.user_input.must),
                "dont": list(ctx.user_input.dont),
                "nice": list(ctx.user_input.nice),
            },
            "context": [  # Mirror project contexts for validator inspection
                {
                    "repo_owner": p.repo_owner,
                    "repo_name": p.repo_name,
                    "ref": p.ref,
                    "tree_json": p.tree_json,
                    "dependency_json": p.dependency_json,
                    "summary_json": p.summary_json,
                }
                for p in ctx.projects
            ],
            "status": "success",
            "prompt_preview": "...",
        }
```

2. To use as the default engine, create a package named `af_prompt_core` with a `PromptEngineBackend` class, or modify the factory function in `prompt_engine.py`.

### Error Handling

When `PromptEngine.run()` raises an exception:
- Errors propagate to the API response with status "failure"
- The response omits `run_id` to indicate no run was created
- Factory import failures are logged but the service continues running with the stub

## Plan Validator Architecture

The planner service treats PromptEngine output as an untrusted candidate that requires validation before sending to clients. The plan validator abstraction sits between the PromptEngine and response serialization.

### PlanValidator Protocol

The `PlanValidator` protocol defines the interface for plan validators:

```python
class PlanValidator(Protocol):
    def validate(self, ctx: PlanningContext, candidate_payload: object) -> dict:
        """Validate the candidate payload from the prompt engine."""
        ...
```

### Available Validators

| Validator | Description |
|-----------|-------------|
| `StubPlanValidator` | Enforces basic structure (dict with `request_id` and `plan_version`) |

### PlanValidationFailure Exception

When validation fails, validators raise `PlanValidationFailure` with:
- `code`: Machine-readable error code for programmatic handling
- `message`: Human-readable error message for debugging

```python
from planner_service.plan_validator import PlanValidationFailure

try:
    validated = validator.validate(ctx, candidate_payload)
except PlanValidationFailure as exc:
    error_response = {"code": exc.code, "message": exc.message}
```

### StubPlanValidator Checks

The stub validator enforces:
1. Payload must be a `dict` (raises `INVALID_PAYLOAD_TYPE`)
2. Payload must contain `request_id` key (raises `MISSING_REQUEST_ID`)
3. Payload must contain `plan_version` key (raises `MISSING_PLAN_VERSION`)
4. `request_id` must be a string (raises `INVALID_REQUEST_ID_TYPE`)
5. `plan_version` must be a string (raises `INVALID_PLAN_VERSION_TYPE`)

### Custom Validator Implementation

To implement a custom plan validator:

```python
from planner_service.plan_validator import PlanValidator, PlanValidationFailure
from planner_service.models import PlanningContext

class MyCustomValidator:
    def validate(self, ctx: PlanningContext, candidate_payload: object) -> dict:
        if not isinstance(candidate_payload, dict):
            raise PlanValidationFailure(
                code="INVALID_PAYLOAD_TYPE",
                message=f"Expected dict, got {type(candidate_payload).__name__}",
            )
        # Additional validation logic...
        return candidate_payload
```

### Integration with PlanningContext

The validator receives the full `PlanningContext` to enable cross-referencing validation (e.g., verifying the payload's `request_id` matches the context). Future validators may use context fields for richer checks.

## Model Contracts (AF v1.1)

### RepositoryPointer

Reference to a specific repository location. The canonical coordinate for a repository consists of owner, name, and ref.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `owner` | string | Yes | - | Repository owner (user or organization) |
| `name` | string | Yes | - | Repository name |
| `ref` | string | No | `refs/heads/main` | Git ref (branch, tag, or commit SHA) |

### UserInput

User-provided input for the planning request. Enforces exactly five required keys with strict typing and validation for string lists.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `purpose` | string | Yes | The purpose or goal of the planning request |
| `vision` | string | Yes | The desired end state or vision for the project |
| `must` | list[string] | Yes | List of requirements that must be fulfilled |
| `dont` | list[string] | Yes | List of constraints or things to avoid |
| `nice` | list[string] | Yes | List of nice-to-have features or improvements |

**Validation Rules:**
- All five keys are required; extra keys are rejected
- List entries must be non-empty strings (no empty or whitespace-only values)

### PlanRequest

Request model for the /v1/plan endpoint.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `repository` | RepositoryPointer | Yes | Target repository |
| `user_input` | UserInput | Yes | User's planning input |
| `request_id` | UUID | No | Client-provided request ID for idempotency |

### PlanResponse

Response model for a successful plan generation.

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | UUID | Request ID (echoed from request or server-generated) |
| `run_id` | UUID | Unique identifier for this planning run |
| `status` | string | Status of the planning operation |
| `payload` | dict | Plan payload (when status is 'completed') |

### ProjectContext (Internal)

Internal artifact carrier for project context. Decoupled from request types for internal runtime use.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `repo_owner` | string | Yes | - | Repository owner (user or organization) |
| `repo_name` | string | Yes | - | Repository name |
| `ref` | string | No | `refs/heads/main` | Git ref (branch, tag, or commit SHA) |
| `tree_json` | string | No | null | JSON string containing repository tree structure |
| `dependency_json` | string | No | null | JSON string containing dependency information |
| `summary_json` | string | No | null | JSON string containing repository summary |

### PlanningContext (Internal)

Full context for a planning operation. Links request_id, UserInput, and a list of ProjectContext entries.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | UUID | Yes | Request identifier for tracking |
| `user_input` | UserInput | Yes | User's input |
| `projects` | list[ProjectContext] | Yes | List of project contexts for planning |

## Logging

The service uses structlog for structured logging with the following features:

- **Service Tag**: All log entries include `service: "planner-service"`
- **Development Mode**: Pretty console output when running in a TTY
- **Production Mode**: JSON output for Cloud Run log aggregation
- **Log Level**: Configurable via `LOG_LEVEL` environment variable

### Event Hooks

Key log events emitted by the service:

| Event | Fields | Description |
|-------|--------|-------------|
| `planner_service_starting` | `version` | Service startup with version info |
| `planner_service_shutting_down` | - | Service shutdown |
| `plan_request_received` | `request_id`, `repository`, `repo_owner`, `repo_name`, `repo_ref`, `user_id` | New planning request received |
| `plan_request_completed` | `request_id`, `run_id`, `repository`, `repo_owner`, `repo_name`, `repo_ref`, `user_id`, `outcome`, `status` | Planning request completed successfully |
| `plan_request_context_failure` | `request_id`, `repository`, `user_id`, `error`, `outcome` | Context driver failure |
| `plan_request_engine_failure` | `request_id`, `repository`, `user_id`, `error`, `outcome` | Prompt engine failure |
| `plan.validation.failed` | `request_id`, `validator_name`, `error_code` | Plan validation failure (structured telemetry) |
| `plan_request_validation_failure` | `request_id`, `repository`, `user_id`, `error_code`, `error`, `outcome` | Plan validation failure (detailed) |
| `auth_header_missing` | `message` | Authorization header missing (warning for future enforcement) |
| `auth_header_invalid_format` | `message` | Invalid authorization format |
| `context_driver_selected` | `driver` | Private context driver selected |
| `context_driver_fallback` | `driver`, `reason` | Fallback to stub context driver |
| `prompt_engine_selected` | `engine` | Private prompt engine selected |
| `prompt_engine_fallback` | `engine`, `reason` | Fallback to stub prompt engine |
| `stub_prompt_engine_run` | `request_id`, `repository`, `session_id` | Stub prompt engine executed |

### Example Log Output

Request received (JSON format):
```json
{
  "event": "plan_request_received",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "repository": "myorg/myrepo",
  "repo_owner": "myorg",
  "repo_name": "myrepo",
  "repo_ref": "main",
  "user_id": "stub-user",
  "service": "planner-service",
  "level": "info",
  "timestamp": "2025-01-01T00:00:00.000000Z"
}
```

Request completed (JSON format):
```json
{
  "event": "plan_request_completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "repository": "myorg/myrepo",
  "repo_owner": "myorg",
  "repo_name": "myrepo",
  "repo_ref": "main",
  "user_id": "stub-user",
  "outcome": "success",
  "status": "ok",
  "service": "planner-service",
  "level": "info",
  "timestamp": "2025-01-01T00:00:00.000001Z"
}
```

Validation failure (JSON format):
```json
{
  "event": "plan.validation.failed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "validator_name": "StubPlanValidator",
  "error_code": "MISSING_REQUEST_ID",
  "service": "planner-service",
  "level": "warning",
  "timestamp": "2025-01-01T00:00:00.000001Z"
}
```

## Running Tests

### Using Makefile

```bash
# Run all tests with verbose output
make test
```

### Manual

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_app.py

# Run specific test class
pytest tests/test_app.py::TestHealthEndpoint
```

## Version Information

The package version is `0.1.0`, defined in `planner_service/__init__.py`. For detailed version metadata, release process, and changelog, see [docs/versioning.md](docs/versioning.md).

## Error Handling

Request payload missing required fields returns a validation error (HTTP 422) with a structured `ErrorResponse` that includes `request_id` for tracking but omits `run_id`:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "repository: Field required"
  },
  "request_id": "uuid"
}
```



# Permanents (License, Contributing, Author)

Do not change any of the below sections

## License

All Agent Foundry work is licensed under the GPLv3 License - see the LICENSE file for details.

## Contributing

Feel free to submit issues and enhancement requests!

## Author

Created by Agent Foundry and John Brosnihan
