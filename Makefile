SHELL := /bin/bash

install:
	poetry update

clean:
	rm -rf dist

test:
	poetry run tox -p -o -r

build:
	poetry build

publish: install test clean build
	poetry run python -mtwine upload dist/* --verbose
