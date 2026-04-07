default: install migrate run

install:
	uv sync

migrate:
	uv run manage.py migrate

run:
	uv run manage.py runserver --settings=alteza_proefopdracht.settings.local

run-tailwind:
	uv run manage.py tailwind start

test:
	uv run manage.py test --settings=alteza_proefopdracht.settings.tests