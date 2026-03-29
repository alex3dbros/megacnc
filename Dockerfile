# Use an official Python runtime as a parent image
FROM python:3.11-bookworm

# WeasyPrint (PDF): Systembibliotheken
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi-dev libjpeg62-turbo libopenjp2-7 \
    libharfbuzz0b fonts-dejavu-core shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "dashboard.wsgi:application"]