$(shell test -s ".env" || cp ".env.example" ".env")
ENVARS := $(shell cat ".env" | xargs)
WITH_ENV = env $(ENVARS)

VENV_BIN = venv/bin/
VENV_PIP = $(VENV_BIN)pip
VENV_PYTEST = $(VENV_BIN)pytest
VENV_PYTHON = $(VENV_BIN)python
VENV_COVERAGE = $(VENV_BIN)coverage
VENV_BLACK = $(VENV_BIN)black
VENV_RELEASE = $(VENV_BIN)semantic-release$(shell [ '$(GITHUB_REF)' = 'master' ] && echo '' || echo ' --noop')

PYTHON_EXEC = $(WITH_ENV) $(VENV_PYTHON)
PYTEST_EXEC = $(WITH_ENV) $(VENV_PYTEST)
COVERAGE_EXEC = $(WITH_ENV) $(VENV_COVERAGE)

PROFILE = $(HOME)/.profile
NVM_DIR = $(HOME)/.nvm
NVSHIM_BIN = env NVM_DIR=$(NVM_DIR) $(HOME)/.nvshim/bin/

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
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -Ur requirements.txt
	$(PYTHON_EXEC) -m python_githooks

.PHONY: clean
clean:
	rm -rf artifacts
	rm -rf build
	rm -rf dist

.PHONY: tests
tests:
	$(PYTEST_EXEC)

.PHONY: test
test:
	$(PYTEST_EXEC) -s -k $(keyword)

.PHONY: coverage
coverage:
	@$(COVERAGE_EXEC) run --source=. -m pytest
	@$(VENV_COVERAGE) html

.PHONY: report
report:
	$(VENV_COVERAGE) xml && $(VENV_BIN)coveralls

.PHONY: run
run:
	$(PYTHON_EXEC) $(py) $(args)

.PHONY: build
build: clean
	@mkdir -p ./artifacts
	@$(PYTHON_EXEC) ./src/compiler

.PHONY: sanity
sanity:
	touch $(PROFILE)
	curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | PROFILE=$(PROFILE) bash
	. $(PROFILE) && nvm install stable
	./dist/installer ~/.nvshim/bin $(PROFILE)
	echo 'lts/dubnium' > .nvmrc
	$(NVSHIM_BIN)node --version | grep -q 'v10.16.3' && echo 'success' || exit 1
	$(NVSHIM_BIN)npm --version | grep -q '6.9.0' && echo 'success' || exit 1
	$(NVSHIM_BIN)npx --version | grep -q '6.9.0' && echo 'success' || exit 1

.PHONY: lint
lint:
	$(VENV_BLACK) . --check

.PHONY: format
format:
	$(VENV_BLACK) .

.PHONY: deploy
deploy:
	echo "$(VENV_RELEASE) publish"

ifndef VERBOSE
.SILENT:
endif
