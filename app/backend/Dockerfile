FROM python:3.9-slim

# Set the PYTHONPATH to include the /app directory
ENV PYTHONPATH=/app

# Set environment variables based on the build arguments
ARG GUNICORN_FLASK
ARG GUNICORN_TIMEOUT
ARG FLASK_RUN_PORT
ARG FLASK_RUN_HOST

ENV GUNICORN_FLASK=${GUNICORN_FLASK}
ENV GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT}
ENV FLASK_RUN_PORT=${FLASK_RUN_PORT}
ENV FLASK_RUN_HOST=${FLASK_RUN_HOST}

# Check if any build arguments are empty
RUN if [ -z "$GUNICORN_FLASK" ]; then echo "Error: GUNICORN_FLASK must be set during build" && exit 1; fi && \
    if [ -z "$GUNICORN_TIMEOUT" ]; then echo "Error: GUNICORN_TIMEOUT must be set during build" && exit 1; fi && \
    if [ -z "$FLASK_RUN_PORT" ]; then echo "Error: FLASK_RUN_PORT must be set during build" && exit 1; fi && \
    if [ -z "$FLASK_RUN_HOST" ]; then echo "Error: FLASK_RUN_HOST must be set during build" && exit 1; fi

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt ./app/requirements.txt
COPY ./app ./app

RUN pip install --no-cache-dir -r ./app/requirements.txt

# Use a Gunicorn command that imports the correct app module
# the llm processes cam take a long time to start up, so we set a timeout of 600 seconds
CMD gunicorn "$GUNICORN_FLASK" --bind "$FLASK_RUN_HOST:$FLASK_RUN_PORT" --timeout "$GUNICORN_TIMEOUT"

