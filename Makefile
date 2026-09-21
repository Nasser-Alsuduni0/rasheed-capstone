PYTHON ?= python
IMAGE ?= rasheed-capstone:dev
BASE_URL ?= http://127.0.0.1:8010

.PHONY: install test test-fast test-slow lint image up down smoke benchmark secrets
install:
	$(PYTHON) -m pip install --require-hashes -r requirements-dev.lock
	$(PYTHON) -m pip install --no-deps -e .

lint:
	ruff check src tests scripts
	ruff format --check src tests scripts
	mypy src
	lint-imports

test:
	$(PYTHON) -m pytest --cov --cov-report=term-missing --cov-report=xml -q

test-fast:
	$(PYTHON) scripts/fast_gate.py

test-slow:
	$(PYTHON) -m pytest -m slow -q

image:
	docker build --tag $(IMAGE) .

up:
	docker compose up --detach --build --wait

down:
	docker compose down --remove-orphans

smoke:
	$(PYTHON) scripts/smoke.py --base-url $(BASE_URL)

benchmark:
	$(PYTHON) scripts/benchmark.py --base-url $(BASE_URL)

secrets:
	gitleaks git . --redact
	gitleaks dir . --redact
