.PHONY: help install dev test lint fmt check examples docs build clean

help:
	@echo "make install   install Rex from source"
	@echo "make dev       install with dev + docs extras"
	@echo "make test      run the test suite"
	@echo "make lint      run ruff"
	@echo "make check     static-check every example with rex check"
	@echo "make examples  run every example"
	@echo "make docs      serve the documentation locally"
	@echo "make build     build a wheel and sdist"
	@echo "make clean     remove build artefacts"

install:
	python -m pip install -e .

dev:
	python -m pip install -e ".[dev,docs]"

test:
	python -m pytest

lint:
	python -m ruff check rex tests

fmt:
	python -m ruff format rex tests

check:
	@for f in examples/*.rex; do python -m rex check "$$f" || exit 1; done

examples:
	@for f in examples/*.rex; do echo "== $$f"; python -m rex run "$$f"; done

docs:
	python -m mkdocs serve

build:
	python -m pip install build
	python -m build

clean:
	rm -rf build dist site .pytest_cache .ruff_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
