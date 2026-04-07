default: install migrate run

install:
	uv sync

migrate:
	uv run manage.py migrate

makemigrations:
	uv run manage.py makemigrations

run:
	uv run manage.py runserver --settings=alteza_proefopdracht.settings.local

run-tailwind:
	uv run manage.py tailwind start

test:
	uv run pytest

reset:
	uv run manage.py flush --no-input
	uv run manage.py migrate
	DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD=admin uv run manage.py createsuperuser --noinput