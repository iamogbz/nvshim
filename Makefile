$(shell test -s ".env" || cp ".env.example" ".env")
ENVARS := $(shell cat ".env" | xargs)
WITH_ENV = env $(ENVARS)

VENV_BIN = venv/bin/
PIP_EXEC = $(VENV_BIN)pip
PYTEST_EXEC = $(WITH_ENV) $(VENV_BIN)pytest
PYTHON_EXEC = $(WITH_ENV) $(VENV_BIN)python
COVERAGE_EXEC = $(WITH_ENV) $(VENV_BIN)coverage
BLACK_EXEC = $(VENV_BIN)black

PYTHON_SETUP = $(PYTHON_EXEC) setup.py

PROFILE = $(HOME)/.profile
NVSHIM_BIN = $(HOME)/.nvshim/bin/

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
	@echo "make setup                        - run pip setup to install shim for development"
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

.PHONY: clean
clean:
	rm -rf artifacts/*
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

.PHONY: tests
tests:
	$(PYTEST_EXEC)

.PHONY: test
test:
	$(PYTEST_EXEC) -s -k $(keyword)

.PHONY: coverage
coverage:
	@$(COVERAGE_EXEC) run --source=. -m pytest
	@$(COVERAGE_EXEC) html

.PHONY: report
report:
	$(COVERAGE_EXEC) xml && $(VENV_BIN)coveralls

.PHONY: run
run:
	$(PYTHON_EXEC) $(py) $(args)

.PHONY: compile
compile: clean
	@$(PYTHON_EXEC) src/nvshim/compiler

.PHONY: sanities
sanities:
	touch $(PROFILE)
	curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | PROFILE=$(PROFILE) bash
	. $(PROFILE) && nvm install stable
	make sanity.setup
	make sanity.compile

.PHONY: sanity.check
sanity.check:
	env NVM_DIR=$(HOME)/.nvm $(exec) --version | grep -q '$(match)' && echo 'success' || exit 1

.PHONY: sanity.setup
sanity.setup:
	$(PYTHON_SETUP) install
	echo 'lts/carbon' > .nvmrc
	make sanity.check exec=node version="v8.16.1"
	make sanity.check exec=npm version="6.4.1"
	make sanity.check exec=npx version="6.4.1"
	rm .nvmrc

.PHONY: sanity.compile
sanity.compile: compile
	./dist/installer $(NVSHIM_BIN) $(PROFILE) ~/.bashrc
	echo 'lts/dubnium' > .nvmrc
	make sanity.check exec=$(NVSHIM_BIN)node version="v10.16.3"
	make sanity.check exec=$(NVSHIM_BIN)npm version="6.9.0"
	make sanity.check exec=$(NVSHIM_BIN)npx version="6.9.0"
	rm .nvmrc

.PHONY: lint
lint:
	$(BLACK_EXEC) . --check

.PHONY: format
format:
	$(BLACK_EXEC) .

.PHONY: setup.debug
setup.debug: clean
	export DISTUTILS_DEBUG=1 && $(PYTHON_SETUP) install -vvv

.PHONY: setup
setup: clean
	@$(PYTHON_SETUP) sdist bdist_wheel

.PHONY: deploy
deploy:
	"$(PYTHON_EXEC) release.py"

ifndef VERBOSE
.SILENT:
endif
