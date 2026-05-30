.PHONY: api streams migrate migration infra-up infra-down install lint format front

api:
	poetry run uvicorn app.presentation.api.app:app --host 0.0.0.0 --port 8000

streams:
	poetry run faststream run app.presentation.streams.__main__:stream_app

migrate:
	poetry run alembic upgrade head

migration:
	poetry run alembic revision --autogenerate -m "$(name)"

infra-up:
	docker compose up -d

infra-down:
	docker compose down

install:
	poetry install

lint:
	poetry run ruff check .

format:
	poetry run ruff format .

front:
	cd front && npm start
