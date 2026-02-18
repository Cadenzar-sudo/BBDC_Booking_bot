# Use Debian 13 (Trixie) slim
FROM debian:trixie-slim

# Prevent Python from buffering stdout/stderr and writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose Gunicorn port
EXPOSE 8000

# Start Gunicorn with 3 workers
# app:app refers to (file_name):(flask_variable_name)
CMD ["gunicorn", "-w", "3", "--bind", "0.0.0.0:8000","--max-requests","500","--max-requests-jitter", "50" ,"wsgi:app"]