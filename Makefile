#
# Makefile for zatodeploy package
#

PKG = zatodeploy
SRCDIR = src
SOURCES = $(wildcard src/$(PKG)/*.py)
TESTS = $(wildcard tests/test_*.py)
LINTME = $(SOURCES) $(TESTS)

# location for the webapp.py we use:
export PYTHONPATH=$(PWD)/src

.PHONY: check flake pylint pylint-report test

all:
	@echo "No default make target."

flake: $(LINTME)
# 	flake8 should read tox.ini by default but it does not
	flake8 --config=tox.ini $^

pylint: $(LINTME)
# 	Pylint exit codes other than 1, 2 and 32 are ignored
	pylint --rcfile=pylint.rc --reports=n $^ || test $$(($$?&35)) -eq 0

pylint-report: $(LINTME)
	pylint --rcfile=pylint.rc $^

check: flake pylint

test:
	nosetests -v tests/test_*

deploy-test:
	cd tests; zato-deploy test1
