.PHONY: install test lint doctor check

install:
	uv sync --extra dev
	pnpm install

test:
	uv run pytest -q
	pnpm --dir slides test

lint:
	uv run ruff check .
	uv run mypy src
	pnpm --dir slides build

doctor:
	uv run paperflow doctor

check: test lint
