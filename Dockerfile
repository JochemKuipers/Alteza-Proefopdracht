FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# System deps needed for typical Python wheels and Django tooling
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl gettext \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip \
    && pip install uv

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --group dev

COPY . /app/

EXPOSE 8000

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=alteza_proefopdracht.settings.local"]
