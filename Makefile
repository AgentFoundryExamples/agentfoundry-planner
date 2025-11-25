# ============================================================
# SPDX-License-Identifier: GPL-3.0-or-later
# This program was generated as part of the AgentFoundry project.
# Copyright (C) 2025  John Brosnihan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ============================================================

# Planner Service Makefile
# Provides developer ergonomics for install, lint, test, and run targets

.PHONY: help install install-dev lint test run clean

# Default target
help:
	@echo "Planner Service Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help        Show this help message"
	@echo "  install     Install package dependencies"
	@echo "  install-dev Install package with dev dependencies"
	@echo "  lint        Run linting with ruff (if available)"
	@echo "  test        Run tests with pytest"
	@echo "  run         Start the development server with uvicorn"
	@echo "  clean       Remove build artifacts and cache files"
	@echo ""
	@echo "Environment Variables:"
	@echo "  PORT          Server port (default: 8080)"
	@echo "  LOG_LEVEL     Logging level (default: INFO)"
	@echo "  DEBUG_AUTH_TOKEN  Token for debug endpoint (default: debug-token-stub)"

# Virtual environment directory
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
UVICORN := $(VENV)/bin/uvicorn
RUFF := $(VENV)/bin/ruff

# Check if virtualenv exists, create if not
$(VENV)/bin/activate:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)

# Install package dependencies
install: $(VENV)/bin/activate
	@echo "Installing package dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -e .
	@echo "Installation complete. Activate with: source $(VENV)/bin/activate"

# Install package with dev dependencies
install-dev: $(VENV)/bin/activate
	@echo "Installing package with dev dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo "Dev installation complete. Activate with: source $(VENV)/bin/activate"

# Run linting with ruff (if available)
lint: $(VENV)/bin/activate
	@if [ -f "$(RUFF)" ]; then \
		echo "Running ruff linter..."; \
		$(RUFF) check .; \
	elif command -v ruff > /dev/null 2>&1; then \
		echo "Running system ruff linter..."; \
		ruff check .; \
	else \
		echo "Ruff not installed. Install with: pip install ruff"; \
		echo "Skipping lint..."; \
	fi

# Run tests with pytest
test: $(VENV)/bin/activate
	@if [ -f "$(PYTEST)" ]; then \
		echo "Running tests with pytest..."; \
		$(PYTEST) -v; \
	else \
		echo "pytest not found in virtualenv. Run 'make install-dev' first."; \
		exit 1; \
	fi

# Start the development server with uvicorn
run: $(VENV)/bin/activate
	@if [ -f "$(UVICORN)" ]; then \
		echo "Starting development server..."; \
		$(UVICORN) planner_service.api:app --reload --host 0.0.0.0 --port $${PORT:-8080}; \
	else \
		echo "uvicorn not found in virtualenv. Run 'make install' first."; \
		exit 1; \
	fi

# Remove build artifacts and cache files
clean:
	@echo "Cleaning build artifacts and cache files..."
	rm -rf $(VENV)
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf __pycache__/
	rm -rf planner_service/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf .coverage
	rm -rf htmlcov/
	@echo "Clean complete."
