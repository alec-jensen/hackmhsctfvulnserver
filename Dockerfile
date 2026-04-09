# Use an official Python image as the base image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies first for better build caching.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy only runtime application files.
COPY admin_store.py /app/admin_store.py
COPY config.py /app/config.py
COPY main.py /app/main.py
COPY schemas.py /app/schemas.py
COPY challenges /app/challenges
COPY ui /app/ui

# Create writable data directory and run as non-root.
RUN addgroup --system app && adduser --system --ingroup app app && \
    mkdir -p /app/data && chown -R app:app /app
USER app

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
