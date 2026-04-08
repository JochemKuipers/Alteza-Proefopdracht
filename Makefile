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
	cmd /C "if exist alteza_proefopdracht\db.sqlite3 del /F /Q alteza_proefopdracht\db.sqlite3"
	uv run manage.py migrate
	uv run manage.py post_reset_db

lint:
	uv run ruff check . --fix

format:
	uv run ruff format .
	uv run djlint --reformat .

makemessages:
	uv run manage.py makemessages -l nl

compilemessages:
	uv run manage.py compilemessages