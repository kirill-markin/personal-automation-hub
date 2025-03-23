FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY run.py .
COPY backend ./backend

# Install Python dependencies using uv
RUN uv pip install --system --no-cache-dir -e "."

# Command to run the application
CMD ["python", "run.py"] 