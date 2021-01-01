.PHONY: virtual install build-requirements black isort flake8 unit-test feature-test sls-deploy sls-remove sls-info

.slsbin/serverless: # Installs serverless framework
	mkdir .slsbin
	curl -L -o .slsbin/serverless https://github.com/serverless/serverless/releases/download/v2.17.0/serverless-linux-x64
	chmod +x .slsbin/serverless

sls-deploy: .slsbin/serverless
	.slsbin/serverless deploy --conceal | tee .slsbin/deploy_output
	grep "/newsletter_signup" .slsbin/deploy_output | cut -d '/' -f3 > .slsbin/test_domain

sls-remove: .slsbin/serverless
	.slsbin/serverless remove
	rm -f .slsbin/test_domain

sls-info: .slsbin/serverless
	.slsbin/serverless info

virtual: .venv/bin/pip # Creates an isolated python 3 environment

.venv/bin/pip:
	virtualenv .venv

install: virtual
	.venv/bin/pip install -Ur requirements.txt

update-requirements: install
	.venv/bin/pip freeze > requirements.txt

.venv/bin/black:
	.venv/bin/pip install -U black

.venv/bin/isort:
	.venv/bin/pip install -U isort

.venv/bin/flake8:
	.venv/bin/pip install -U flake8

.venv/bin/pytest:
	.venv/bin/pip install -U pytest

.venv/bin/pytest-bdd:
	.venv/bin/pip install -U pytest-bdd

black: .venv/bin/black # Formats code with black
	.venv/bin/black . --check

isort: .venv/bin/isort # Sorts imports using isort
	.venv/bin/isort . --check-only

flake8: .venv/bin/flake8 # Lints code using flake8
	flake8 --exclude .git,__pycache__,.venv

conformity-tests: black isort flake8

unit-tests: .venv/bin/pytest # Runs unit tests
	.venv/bin/pytest tests/unit

feature-tests: .venv/bin/pytest-bdd # Runs feature tests
	TEST_DOMAIN=$(shell cat .slsbin/test_domain) .venv/bin/py.test tests/features --gherkin-terminal-reporter-expanded

ci-tests:
	mkdir test-results
	TEST_DOMAIN=$(shell cat .slsbin/test_domain) .venv/bin/pytest --junitxml=test-results/junit.xml