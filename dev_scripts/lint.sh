#!/bin/bash
set -ex

poetry run python -m flake8 heimdallm/
poetry run black --check --diff heimdallm/
poetry run mypy heimdallm