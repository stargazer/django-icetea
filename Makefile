COVERAGE=coverage
PYTHON=python

clobber:
	@echo "---> Cleaning project"
	find $(CURDIR) -name "*.pyc" -type f -delete
	find $(CURDIR) -type d -name __pycache__ -delete
	rm -rf $(CURDIR)/build
	rm -rf $(CURDIR)/dist
	rm -rf $(CURDIR)/django_icetea.egg-info
	$(COVERAGE) erase

test:
	@echo "---> Running tests"
	$(PYTHON) $(CURDIR)/tests/runtests.py --failfast --traceback

test-coverage:
	@echo "---> Running tests (with coverage)"
	$(COVERAGE) run --include "icetea/*" $(CURDIR)/tests/runtests.py
	$(COVERAGE) html

lint:
	flake8 $(CURDIR)/icetea

test-tox:
	tox
