# Planner Service

FastAPI planner service for Agent Foundry. This service provides a planning API endpoint that accepts repository and user input context, returning planning operations with request and run tracking identifiers.

## Features

- FastAPI-based REST API with OpenAPI documentation
- Pydantic models for request/response validation
- Structured logging with structlog (service-tagged)
- Cloud Run ready with health check endpoint
- Environment-based configuration with safe defaults

## Project Structure

```
planner-service/
├── planner_service/
│   ├── __init__.py      # Package initialization
│   ├── api.py           # FastAPI application and endpoints
│   ├── logging.py       # Structlog configuration
│   └── models.py        # Pydantic data models
├── tests/
│   └── test_app.py      # Unit and integration tests
├── Dockerfile           # Cloud Run deployment
├── pyproject.toml       # Project metadata and dependencies
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
