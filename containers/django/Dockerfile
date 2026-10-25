FROM python:3.14-slim

ARG PROJECT_ENV=development

ENV PROJECT_ENV=${PROJECT_ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=2.5.1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_NO_INTERACTION=1

# build-essential is needed to compile uWSGI (no wheels are published).
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /code
COPY src/pyproject.toml src/poetry.lock /code/

# Project initialization:
RUN if [ "$PROJECT_ENV" = "production" ]; then \
    poetry install --no-root --only main --no-ansi; \
  else \
    poetry install --no-root --no-ansi; \
  fi

COPY src/ /code/
