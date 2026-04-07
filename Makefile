default: install migrate run

install:
	uv sync

migrate:
	uv run python manage.py migrate

run:
	uv run python manage.py runserver --settings=alteza_proefopdracht.settings.local

test:
	uv run python manage.py test --settings=alteza_proefopdracht.settings.tests