FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy application code
COPY planner_service/ ./planner_service/

# Set environment variables
ENV PORT=8080
ENV LOG_LEVEL=INFO

# Expose port for Cloud Run
EXPOSE 8080

# Run uvicorn server
CMD ["uvicorn", "planner_service.api:app", "--host", "0.0.0.0", "--port", "8080"]
