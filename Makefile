$(shell test -s ".env" || cp ".env.example" ".env")
ENVARS := $(shell cat ".env" | xargs)
WITH_ENV = env $(ENVARS)

VENV_BIN = venv/bin/
PIP_EXEC = $(VENV_BIN)pip
PYTEST_EXEC = $(WITH_ENV) $(VENV_BIN)pytest
PYTHON_EXEC = $(WITH_ENV) $(VENV_BIN)python
COVERAGE_EXEC = $(WITH_ENV) $(VENV_BIN)coverage
BLACK_EXEC = $(VENV_BIN)black

RELEASE_FLAGS = $(shell [ '$(GITHUB_REF)' = 'refs/heads/master' ] && echo '' || echo ' --noop')
RELEASE_EXEC = $(VENV_BIN)semantic-release$(RELEASE_FLAGS)

PROFILE = $(HOME)/.profile
NVM_DIR = $(HOME)/.nvm
NVSHIM_BIN = $(HOME)/.nvshim/bin/
NVSHIM_EXEC = env NVM_DIR=$(NVM_DIR) $(NVSHIM_BIN)

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
	@echo "make dist                         - make distributables for release"
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
coverage: src
	@$(COVERAGE_EXEC) run --source=. -m pytest
	@$(COVERAGE_EXEC) html

.PHONY: report
report:
	$(COVERAGE_EXEC) xml && $(VENV_BIN)coveralls

.PHONY: run
run:
	$(PYTHON_EXEC) $(py) $(args)

build: src
	make clean
	@$(PYTHON_EXEC) ./src/compiler
	@touch build

dist: build
	dist/installer dist
	@$(PYTHON_EXEC) setup.py sdist bdist_wheel
	@touch dist

.PHONY: sanity
sanity:
	touch $(PROFILE)
	curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | PROFILE=$(PROFILE) bash
	. $(PROFILE) && nvm install stable
	./dist/installer $(NVSHIM_BIN) $(PROFILE)
	echo 'lts/dubnium' > .nvmrc
	$(NVSHIM_EXEC)node --version | grep -q 'v10.16.3' && echo 'success' || exit 1
	$(NVSHIM_EXEC)npm --version | grep -q '6.9.0' && echo 'success' || exit 1
	$(NVSHIM_EXEC)npx --version | grep -q '6.9.0' && echo 'success' || exit 1

.PHONY: lint
lint:
	$(BLACK_EXEC) . --check

.PHONY: format
format:
	$(BLACK_EXEC) .

.PHONY: deploy
deploy:
	$(RELEASE_EXEC) publish

ifndef VERBOSE
.SILENT:
endif
