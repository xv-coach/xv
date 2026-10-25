FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/

ARG PROJECT_ENV=development

# The venv lives outside /code because docker-compose bind-mounts ./src
# over /code in development.
ENV PROJECT_ENV=${PROJECT_ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  UV_PROJECT_ENVIRONMENT=/opt/venv \
  UV_PYTHON_DOWNLOADS=never \
  UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy \
  PATH="/opt/venv/bin:$PATH"

# build-essential is needed to compile uWSGI (no wheels are published).
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Install dependencies first for better layer caching.
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=src/uv.lock,target=uv.lock \
  --mount=type=bind,source=src/pyproject.toml,target=pyproject.toml \
  if [ "$PROJECT_ENV" = "production" ]; then \
    uv sync --locked --no-install-project --no-dev; \
  else \
    uv sync --locked --no-install-project; \
  fi

COPY src/ /code/
