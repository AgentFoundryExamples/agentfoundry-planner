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
│   ├── __init__.py         # Package initialization
│   ├── api.py              # FastAPI application and endpoints
│   ├── context_driver.py   # Context driver abstraction and factory
│   ├── logging.py          # Structlog configuration
│   ├── models.py           # Pydantic data models
│   ├── prompt_engine.py    # Prompt engine abstraction and factory
│   └── resources/
│       └── mock_context.json  # Mock context fixtures
├── tests/
│   ├── test_app.py         # Unit and integration tests
│   ├── test_context_driver.py  # Context driver tests
│   └── test_prompt_engine.py   # Prompt engine tests
├── Dockerfile              # Cloud Run deployment
├── pyproject.toml          # Project metadata and dependencies
└── README.md
```

## Installation

### Prerequisites

- Python 3.11+
- pip

### Install Dependencies

```bash
# Install package with dependencies
pip install -e .

# Install with dev dependencies (for testing)
pip install -e ".[dev]"
```

## Running the Server

### Local Development

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
```

Returns service health status. Available even when downstream stubs fail to initialize.

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

Create a new planning request.

**Request Body:**
```json
{
  "repository": {
    "owner": "string",
    "repo": "string",
    "ref": "string (optional)"
  },
  "user_input": {
    "query": "string",
    "context": "string (optional)"
  },
  "request_id": "uuid (optional)"
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "run_id": "uuid",
  "status": "pending",
  "steps": null
}
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

**Request Body:**
```json
{
  "owner": "string",
  "repo": "string",
  "ref": "string (optional)"
}
```

**Response:**
```json
{
  "repository": {
    "owner": "string",
    "repo": "string",
    "ref": "string"
  },
  "default_branch": "main",
  "languages": ["python"]
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
        # Your implementation here
        return ProjectContext(
            repository=repo,
            default_branch="main",
            languages=["python"],
        )
```

2. To use as the default driver, create a package named `af_github_core` with a `GitHubContextDriver` class, or modify the factory function in `context_driver.py`.

### Mock Context Fixtures

The `StubContextDriver` loads mock data from `planner_service/resources/mock_context.json`. The fixture format is:

```json
{
  "default": {
    "default_branch": "main",
    "languages": ["python"]
  },
  "repositories": {
    "owner/repo": {
      "default_branch": "develop",
      "languages": ["typescript", "rust"]
    }
  }
}
```

- `default`: Default context returned for unknown repositories
- `repositories`: Specific context for known repositories (keyed by `owner/repo`)

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
    "repo": "string",
    "ref": "string|null"
  },
  "status": "success",
  "prompt_preview": "[STUB] Planning request for owner/repo: query..."
}
```

- `request_id`: Unique identifier generated for each request
- `repository`: Repository metadata from the planning context
- `status`: Always "success" for stub (real engines may return "failure")
- `prompt_preview`: Stub preview that does not expose real prompts (useful for wiring tests)

### Custom Engine Implementation

To implement a custom prompt engine:

1. Create a class implementing the `PromptEngine` protocol:

```python
from planner_service.prompt_engine import PromptEngine
from planner_service.models import PlanningContext

class MyCustomEngine:
    def run(self, ctx: PlanningContext) -> dict:
        # Your implementation here (may call LLM, rules engine, etc.)
        return {
            "request_id": "generated-uuid",
            "repository": {
                "owner": ctx.project.repository.owner,
                "repo": ctx.project.repository.repo,
                "ref": ctx.project.repository.ref,
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

## Model Contracts

### RepositoryPointer

Reference to a specific repository location.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `owner` | string | Yes | Repository owner (user or organization) |
| `repo` | string | Yes | Repository name |
| `ref` | string | No | Git ref (branch, tag, or commit SHA) |

### UserInput

User-provided input for the planning request.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | The user's planning query or request |
| `context` | string | No | Additional context provided by the user |

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
| `steps` | list[PlanStep] | Generated plan steps (when status is 'completed') |

### ProjectContext

Context about the project being planned.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `repository` | RepositoryPointer | Yes | Target repository |
| `default_branch` | string | No | Default branch of the repository |
| `languages` | list[string] | No | Primary programming languages |

### PlanningContext

Full context for a planning operation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project` | ProjectContext | Yes | Project context |
| `user_input` | UserInput | Yes | User's input |
| `session_id` | string | No | Session identifier for tracking |

## Logging

The service uses structlog for structured logging with the following features:

- **Service Tag**: All log entries include `service: "planner-service"`
- **Development Mode**: Pretty console output when running in a TTY
- **Production Mode**: JSON output for Cloud Run log aggregation
- **Log Level**: Configurable via `LOG_LEVEL` environment variable

### Event Hooks

Key log events emitted by the service:

| Event | Description |
|-------|-------------|
| `planner_service_starting` | Service startup with version info |
| `planner_service_shutting_down` | Service shutdown |
| `plan_request_received` | New planning request with request_id and run_id |
| `context_driver_selected` | Private context driver selected |
| `context_driver_fallback` | Fallback to stub context driver |
| `prompt_engine_selected` | Private prompt engine selected |
| `prompt_engine_fallback` | Fallback to stub prompt engine |
| `stub_prompt_engine_run` | Stub prompt engine executed with request metadata |

## Running Tests

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

## Error Handling

Request payload missing required fields returns a validation error (HTTP 422) with clear error JSON that omits `run_id`:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "repository"],
      "msg": "Field required"
    }
  ]
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
