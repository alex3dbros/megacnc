# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/


# Copy entrypoint script into the image
COPY entrypoint.sh /usr/src/app/entrypoint.sh

# Run the entrypoint script
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
