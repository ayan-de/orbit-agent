.PHONY: install dev test lint migrate

install:
	pip install -e .

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	black .
	flake8 .

migrate:
	alembic upgrade head
