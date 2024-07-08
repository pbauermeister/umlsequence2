# Just type 'make' to get help.

# Rules
# -----

.PHONY: *

# To have a target explained by 'make [help]', have the form:
#   target: [dependencies] ## help text

################################################################################
# Basic targets

help:	## print this help
        # (display help for targets with comment '##')
	@echo "usage: make COMMAND"
	@echo
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-24s %s\n", $$1, $$2}'

clean: ## remove temporary files
	rm -rf .tmp .mypy_cache tests/mordor install build dist
	rm -rf src/*.egg-info
	find -type d -name __pycache__ -exec rm -rf {} \; || true

black: clean ## apply the black formatter
	black --skip-string-normalization --exclude .venv .

lint: ## lint all python files
	scripts/lint.sh

tests: ## run tests
	cd tests && ./run-tests.sh

uninstall: ## uninstall
	pip3 uninstall -y umlsequence2 2>/dev/null || sudo pip3 uninstall -y umlsequence2

build: ## build
	pip install --upgrade setuptools
	python3 setup.py build

install-locally: clean uninstall build ## build and reinstall locally
	python3 setup.py install
	pip show umlsequence2

doc: ## make diagrams of doc
	scripts/make-doc.sh

all: black lint install-locally tests doc ## Run all the above
	@echo
	@echo "=> OK, all done successfully."

publish-to-pypi: all ## publish to pypi
	scripts/publish-to-pypi.sh
