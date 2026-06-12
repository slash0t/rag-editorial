FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry>=2.0,<3.0"

# Install dependencies first so this layer is cached between source changes
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --without dev

# Copy the application source
COPY . .

# No CMD on purpose: api and streams share this one image and the run command
# is provided per-service at startup (see docker/app.yml).