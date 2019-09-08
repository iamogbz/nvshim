$(shell test -s ".env" || cp ".env.example" ".env")
ENVARS := $(shell cat ".env" | xargs)
VENV_BIN = venv/bin/
PIP_EXEC = $(VENV_BIN)pip
PYTHON_EXEC = env $(ENVARS) $(VENV_BIN)python
PYTEST_EXEC = env $(ENVARS) pytest

.PHONY: upstream
upstream:
	@git remote add upstream https://github.com/iamogbz/py-boilerplate
	@git push origin master
	@git push --all
	@echo "upstream: remote successfully configured"

.PHONY: eject
eject:
	@git fetch --all --prune
	@git checkout -b boilerplate-ejection
	@git pull upstream master --allow-unrelated-histories --no-edit -Xours
	@git pull upstream boilerplate-ejection --no-edit -Xours
	@git reset master --soft && git add --all && git commit -m "chore: eject" -n
	@echo "eject: branch created, complete by replacing placeholder values"

.PHONY: help
help:
	@echo "make help                         - show commands that can be run"
	@echo "make install                      - install project requirements"
	@echo "make test keyword='Parse'         - run only test match keyword"
	@echo "make tests                        - run all tests"
	@echo "make coverage                     - run all tests and collect coverage"
	@echo "make build                        - build executable from src"
	@echo "make deploy                       - run semantic release on built distributables"

.PHONY: venv
venv:
	test -d venv || python3 -m venv venv
	touch $(VENV_BIN)activate

.PHONY: install
install: venv
	$(PIP_EXEC) install --upgrade pip
	$(PIP_EXEC) install -Ur requirements.txt
	$(PYTHON_EXEC) -m python_githooks

.PHONY: tests
tests:
	$(PYTEST_EXEC)

.PHONY: test
test:
	$(PYTEST_EXEC) -s -k $(keyword)

.PHONY: coverage
coverage:
	@env $(ENVARS) coverage run --source=. -m pytest
	@coverage html

.PHONY: run
run:
	$(PYTHON_EXEC) ./src/nvshim $(args)

.PHONY: build
build:
	@mkdir -p ./artifacts
	@$(PYTHON_EXEC) ./src/build

.PHONY: lint
lint:
	black . --check

.PHONY: format
format:
	black .

.PHONY: deploy
deploy:
	echo "Run semantic release"

ifndef VERBOSE
.SILENT:
endif
