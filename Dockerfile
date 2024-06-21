# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# Create a directory for the application
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update \
    && apt-get install -y build-essential \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the application port
EXPOSE 5050

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "main:app", "--workers", "4", "--threads", "2"]

