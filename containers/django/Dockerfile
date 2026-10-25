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
  DJANGO_STATIC_ROOT=/static \
  PATH="/opt/venv/bin:$PATH"

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

RUN useradd --create-home --uid 1000 app \
  && mkdir -p /static \
  && chown app:app /static
USER app

EXPOSE 8000

# Extra gunicorn options (e.g. --reload, --workers 4) can be passed via
# the GUNICORN_CMD_ARGS environment variable.
CMD ["sh", "-c", "python manage.py collectstatic --noinput && exec gunicorn xv_rugby.wsgi:application --bind 0.0.0.0:8000 --access-logfile -"]
