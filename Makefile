.PHONY: help venv install run lint format format-check test clean

VENV := .venv
PYTHON := $(VENV)/bin/python

help:
	@echo "Available targets:"
	@echo "  make venv          - create the virtualenv (.venv)"
	@echo "  make install       - install the package (editable) with dev dependencies"
	@echo "  make run           - launch the app (python -m labyrinthes.app)"
	@echo "  make lint          - run ruff check"
	@echo "  make format        - run ruff format"
	@echo "  make format-check  - check formatting without modifying files"
	@echo "  make test          - run the test suite (pytest)"
	@echo "  make clean         - remove caches and bytecode"

venv:
	python3 -m venv $(VENV) --upgrade-deps

install: venv
	$(PYTHON) -m pip install -e . --group dev

run:
	$(PYTHON) -m labyrinthes.app

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

format-check:
	$(PYTHON) -m ruff format --check .

test:
	$(PYTHON) -m pytest

clean:
	find . -type d -name '__pycache__' -not -path './.venv/*' -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
