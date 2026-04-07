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