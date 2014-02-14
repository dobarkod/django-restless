SETUP=python setup.py

.PHONY: all build test coverage docs clean

all: build coverage docs

build:
	$(SETUP) build

test:
	$(SETUP) test

coverage:
	$(SETUP) coverage

docs:
	rm -rf docs/_build/
	$(SETUP) build_sphinx
	cd docs/_build/html && zip -r ../docs.zip *
	@echo "Documentation packaged to docs/_build/docs.zip"

upload: build coverage docs
	$(SETUP) sdist upload
