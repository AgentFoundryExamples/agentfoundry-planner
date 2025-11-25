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
│   ├── prompt_engine.py    # Prompt engine abstraction and factory
│   └── resources/
│       └── mock_context.json  # Mock context fixtures
├── tests/
│   ├── test_app.py         # Unit and integration tests
│   ├── test_context_driver.py  # Context driver tests
│   ├── test_plan_endpoint.py   # Plan endpoint tests
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

Create a new planning request. This endpoint accepts a planning request, fetches repository context using the context driver, invokes the prompt engine, and returns a plan response with tracking identifiers.

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
  "status": "completed",
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

Note: In the synchronous flow, `run_id` mirrors `request_id`. The `status` is "completed" when the prompt engine succeeds.

**Error Response (5xx):**
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
        return ProjectContext(
            repo_owner=repo.owner,
            repo_name=repo.name,
            ref=repo.ref,
            tree_json=None,
            dependency_json=None,
            summary_json=None,
        )
```

2. To use as the default driver, create a package named `af_github_core` with a `GitHubContextDriver` class, or modify the factory function in `context_driver.py`.

### Mock Context Fixtures

The `StubContextDriver` loads mock data from `planner_service/resources/mock_context.json`. The fixture format is:

```json
{
  "default": {
    "tree_json": null,
    "dependency_json": null,
    "summary_json": null
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

- `default`: Default context returned for unknown repositories
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
  "repository": {
    "owner": "string",
    "name": "string",
    "ref": "refs/heads/main"
  },
  "status": "success",
  "prompt_preview": "[STUB] Planning request for owner/name: purpose text..."
}
```

- `request_id`: The request ID from PlanningContext (matches top-level response ID)
- `repository`: Repository metadata from the planning context (uses AF v1.1 field names)
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
        return {
            "request_id": str(ctx.request_id),
            "repository": {
                "owner": repo_owner,
                "name": repo_name,
                "ref": repo_ref,
            },
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
  "status": "completed",
  "service": "planner-service",
  "level": "info",
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
