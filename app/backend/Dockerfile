FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY ./app ./app
RUN pip install --no-cache-dir -r ./app/backend/requirements.txt

# Set the PYTHONPATH to include the /app directory
ENV PYTHONPATH=/app

# Use a Gunicorn command that imports the correct app module
# the llm processes cam take a long time to start up, so we set a timeout of 600 seconds
CMD ["gunicorn", "app.app:flask_app", "--bind", "0.0.0.0:5000", "--timeout", "600"]
