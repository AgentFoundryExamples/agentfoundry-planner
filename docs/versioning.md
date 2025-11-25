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

### v0.1.0 (Initial Release)

- FastAPI-based REST API with OpenAPI documentation
- Pydantic models for request/response validation
- Structured logging with structlog (service-tagged)
- Cloud Run ready with health check endpoint (`/health`, `/healthz`)
- Environment-based configuration with safe defaults
- Extensible context driver architecture with stub implementation
- Extensible prompt engine architecture with stub implementation
- `/v1/plan` endpoint for creating planning requests
- `/v1/debug/context` endpoint for debugging context fetching
- Makefile with install/lint/test/run targets
- Documentation for environment variables and Docker usage
