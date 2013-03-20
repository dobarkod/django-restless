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
	$(SETUP) build_sphinx

upload: build coverage docs
	$(SETUP) sdist upload
