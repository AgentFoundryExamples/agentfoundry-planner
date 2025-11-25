# Versioning and Release Notes

This document describes the versioning strategy and release process for the Planner Service.

## Version Metadata

The package version is defined in a single source of truth location:

- **Primary**: `planner_service/__init__.py` - Contains `__version__` variable
- **Synchronized**: `pyproject.toml` - Contains `version` field under `[project]`

Both files must be updated together when bumping the version.

### Current Version

The current version is **0.1.0**.

### Version Format

This project follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

### Accessing Version at Runtime

```python
from planner_service import __version__
print(__version__)  # "0.1.0"
```

Or via the health endpoint:

```bash
curl http://localhost:8080/health
# {"status": "healthy", "service": "planner-service", "version": "0.1.0"}
```

## Release Process

### Pre-release Checklist

1. Update version in both locations:
   - `planner_service/__init__.py`: Update `__version__ = "X.Y.Z"`
   - `pyproject.toml`: Update `version = "X.Y.Z"`

2. Run all tests:
   ```bash
   make test
   ```

3. Run linting (if ruff is installed):
   ```bash
   make lint
   ```

4. Verify the server starts correctly:
   ```bash
   make run
   ```

5. Test Docker build:
   ```bash
   docker build -t planner-service .
   docker run -p 8080:8080 planner-service
   ```

6. Verify health endpoint returns new version:
   ```bash
   curl http://localhost:8080/health
   ```

### Tagging a Release

```bash
# Create and push a tag
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

## Changelog

### v0.1.0 (AF v1.1 Contract Update)

**Breaking Changes:**
- **RepositoryPointer**: Renamed `repo` field to `name`. The canonical coordinate is now `(owner, name, ref)`.
- **RepositoryPointer**: `ref` field now defaults to `refs/heads/main` instead of `null`.
- **UserInput**: Complete schema change. Now requires exactly five keys:
  - `purpose` (string): The purpose or goal of the planning request
  - `vision` (string): The desired end state or vision for the project
  - `must` (list[string]): List of requirements that must be fulfilled
  - `dont` (list[string]): List of constraints or things to avoid
  - `nice` (list[string]): List of nice-to-have features or improvements
  - Old fields `query` and `context` are no longer supported.
- **UserInput**: Strict validation enforces non-empty strings in list entries.
- **UserInput**: Extra keys are rejected (strict schema enforcement).
- **ProjectContext**: Redesigned as internal artifact carrier:
  - New fields: `repo_owner`, `repo_name`, `ref`, `tree_json`, `dependency_json`, `summary_json`
  - Old fields `repository`, `default_branch`, `languages` are no longer supported.
- **PlanningContext**: Redesigned structure:
  - New fields: `request_id`, `user_input`, `projects` (list of ProjectContext)
  - Old fields `project`, `session_id` are no longer supported.
- **PlanResponse**: Replaced `steps` field with `payload` field.

**Migration Guide:**

1. **RepositoryPointer**:
   ```python
   # Before
   {"owner": "org", "repo": "name", "ref": null}
   
   # After
   {"owner": "org", "name": "name", "ref": "refs/heads/main"}
   ```

2. **UserInput**:
   ```python
   # Before
   {"query": "Add feature X", "context": "Optional context"}
   
   # After
   {
       "purpose": "Add feature X",
       "vision": "End state description",
       "must": ["Requirement 1", "Requirement 2"],
       "dont": ["Constraint 1"],
       "nice": ["Nice-to-have 1"]
   }
   ```

3. **ProjectContext** (internal):
   ```python
   # Before
   {"repository": {...}, "default_branch": "main", "languages": ["python"]}
   
   # After
   {
       "repo_owner": "org",
       "repo_name": "name",
       "ref": "refs/heads/main",
       "tree_json": null,
       "dependency_json": null,
       "summary_json": null
   }
   ```

4. **PlanningContext** (internal):
   ```python
   # Before
   {"project": {...}, "user_input": {...}, "session_id": "..."}
   
   # After
   {"request_id": "uuid", "user_input": {...}, "projects": [{...}]}
   ```

**Features:**
- FastAPI-based REST API with OpenAPI documentation
- Pydantic models for request/response validation
- Structured logging with structlog (service-tagged)
- Cloud Run ready with health check endpoint (`/health`, `/healthz`)
- Environment-based configuration with safe defaults
- Extensible context driver architecture with stub implementation
- Extensible prompt engine architecture with stub implementation
- Extensible plan validator architecture for validating prompt engine output
- `/v1/plan` endpoint for creating planning requests
- `/v1/debug/context` endpoint for debugging context fetching
- Makefile with install/lint/test/run targets
- Documentation for environment variables and Docker usage

**Validation Pipeline (AF v1.1):**

All `/v1/plan` requests flow through a validator-driven pipeline that treats prompt output as untrusted data:

```
PlanRequest → PlanningContext → PromptEngine → PlanValidator → PlanResponse
```

1. **PlanRequest**: Validated on entry (Pydantic schema enforcement)
2. **PlanningContext**: Constructed from request_id, user_input, and project contexts
3. **PromptEngine**: Generates candidate payload (untrusted)
4. **PlanValidator**: Validates candidate payload structure and semantics
5. **PlanResponse**: Returned only if validation passes

**Error Handling Invariants (AF v1.1):**

- **`request_id`**: Always present in responses (echoed from client or server-generated)
- **`run_id`**: Present only in success responses; absent in all error cases
- **Validation failures**: Return HTTP 422 with `ErrorResponse` schema
- **Context/Engine failures**: Return HTTP 500 with `ErrorResponse` schema

**Repository Coordinate Terminology:**

Consumers referencing the old `repo` field should migrate to the new `owner/name/ref` terminology:

| Old Field | New Field | Notes |
|-----------|-----------|-------|
| `repo` | `name` | Repository name within the owner's namespace |
| `ref: null` | `ref: "refs/heads/main"` | Explicit default instead of null |

The canonical coordinate tuple is now `(owner, name, ref)` for all repository references.

## Plan Validator Module

The `plan_validator` module provides the abstraction for validating candidate payloads from the prompt engine before they are serialized and sent to clients.

### Components

- **`PlanValidationFailure`**: Exception with `code` (machine-readable) and `message` (human-readable) attributes
- **`PlanValidator`**: Protocol defining `validate(ctx, candidate_payload) -> dict`
- **`StubPlanValidator`**: Implementation enforcing `dict` payloads with `request_id` and `plan_version` keys

### Validator Expectations

When implementing a custom validator:

1. Accept `PlanningContext` and a candidate payload (any type)
2. Return the validated payload as a `dict` if valid
3. Raise `PlanValidationFailure` with descriptive `code` and `message` on failure
4. Use well-known error codes for common failures:
   - `INVALID_PAYLOAD_TYPE`: Payload is not the expected type
   - `MISSING_REQUEST_ID`: Required `request_id` key is missing
   - `MISSING_PLAN_VERSION`: Required `plan_version` key is missing
   - `INVALID_REQUEST_ID_TYPE`: `request_id` is not a string
   - `INVALID_PLAN_VERSION_TYPE`: `plan_version` is not a string

### Integration

The validator sits in the pipeline between the PromptEngine and response serialization:

```
Request → ContextDriver → PromptEngine → PlanValidator → Response
```

Future validators may perform deeper checks such as schema validation, business rule enforcement, or cross-referencing against the `PlanningContext`.

## Response Invariants (AF v1.1)

### run_id/request_id Semantics

The AF v1.1 contract enforces strict rules about when `run_id` is present or absent:

| Response Type | `request_id` | `run_id` | Description |
|---------------|--------------|----------|-------------|
| **Success (200)** | ✅ Present | ✅ Present | Planning completed successfully |
| **Validation Error (422)** | ✅ Present | ❌ Absent | Input or plan validation failed |
| **Server Error (5xx)** | ✅ Present | ❌ Absent | Context driver or engine failure |

**Key Invariant**: `run_id` is only included in success responses. Error responses omit `run_id` to indicate that no planning run was created.

### Error Response Structure

All error responses follow the `ErrorResponse` schema:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description"
  },
  "request_id": "uuid"
}
```

### Validator Failure Behavior

When `PlanValidator.validate()` raises `PlanValidationFailure`:

1. The API returns HTTP 422 (Unprocessable Entity)
2. The response includes `request_id` for tracking
3. The response omits `run_id` (no run was created)
4. The error code and message from the exception are surfaced in the response

Example validation failure response:

```json
{
  "error": {
    "code": "MISSING_REQUEST_ID",
    "message": "Payload missing required key: request_id"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Future Extensions

### validate_only Mode (Reserved)

A future iteration may introduce an optional `validate_only` parameter on `/v1/plan` requests. When enabled:

- The request would go through context fetching and prompt engine execution
- Validation would be performed on the candidate payload
- The response would indicate validation success/failure without persisting a run
- This mode would be useful for testing and dry-run scenarios

**Note**: This feature is not currently implemented. The parameter name and behavior are reserved for future use.
