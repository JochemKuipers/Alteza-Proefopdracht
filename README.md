# Alteza Proefopdracht

A Django application to **fetch and display GitHub commits** for a specified repository.

## Features

- **Repository search suggestions** (GitHub search)
- **Commit listing API** with pagination and filtering (branch, date range, author)
- **Optional “group by author”** view on the API
- **GitHub OAuth login** via `django-allauth` (uses the logged-in user’s token when available)
- **Tailwind** styling via `django-tailwind`

## Tech stack

- **Python**: 3.14+
- **Django**: 6.x
- **HTTP**: `PyGithub` + `httpx`
- **API**: Django REST Framework (DRF)
- **Tooling**: `uv`, `pytest`, `ruff`, `djlint`

## Local development (recommended)

### Prerequisites

- **Python 3.14+**
- **uv** installed (see `https://docs.astral.sh/uv/`)
- (Optional) **GNU Make** (or use the equivalent commands shown below)

### Install deps

```bash
make install
```

Equivalent without `make`:

```bash
uv sync
```

### Database setup

```bash
make migrate
```

### Run the app

```bash
make run
```

This runs Django with `alteza_proefopdracht.settings.local` and starts the server on `http://127.0.0.1:8000/`.

### Tailwind

Its imporant to run this at least once for the first run to build the styling.
If you’re actively changing styles, run the Tailwind watcher in a second terminal:

```bash
make run-tailwind
```

## Usage

### UI

- **Home**: `/` (repo selector + UI that calls the API endpoints)
- **Auth**: `/accounts/` (allauth)
- **Profile**: `/accounts/profile/`

### API

- **Repo suggestions**: `GET /api/repo-suggest/?q=<search>`
- **Commits**: `GET /api/commits/?repo=owner/repo`

Common query params for `/api/commits/`:

- `repo` (required): `owner/repo`
- `branch` (optional)
- `start_date` / `end_date` (optional, `YYYY-MM-DD`)
- `author` (optional, exact match)
- `group_by_author` (optional boolean-ish)
- `page` (optional, default `1`)

## Quality

### Tests

```bash
make test
```

Tests use `DJANGO_SETTINGS_MODULE=alteza_proefopdracht.settings.tests` (also set in `pyproject.toml`).

### Lint / format

```bash
make lint-check
make format-check
```

Auto-fix / reformat locally:

```bash
make lint
make format
```

## Reset local DB (SQLite)

```bash
make reset
```

This deletes `alteza_proefopdracht/db.sqlite3`, runs migrations, and then runs `post_reset_db`.

## Docker

The repo ships with a `Dockerfile` and `docker-compose.yml`.

### Run the web app

```bash
docker compose up --build
```

### Run Tailwind watcher (optional)

```bash
docker compose up --build tailwind
```

Notes:

- The compose setup mounts `./alteza_proefopdracht/settings/.env` read-only into the container, so make sure it exists.

## CI

GitHub Actions runs:

- `make lint-check`
- `make format-check`
- `make test`

using **Python 3.14** and `uv sync --frozen --group dev`.
