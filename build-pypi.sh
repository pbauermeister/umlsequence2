#!/bin/sh
#
# Pip packaging:
#   https://packaging.python.org/tutorials/packaging-projects/
#
# Entry point:
#   https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html
#
# Getting a token:
#   https://pypi.org/manage/account/token/

set -ex

rm -rf dist/ src/*.egg-info/
python3 -m build
python3 -m twine upload --username __token__ dist/*
