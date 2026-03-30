# Stage 1: Dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies into a virtualenv
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Production runtime
FROM python:3.12-slim

WORKDIR /app

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY app/ .

# Use virtualenv binaries
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
