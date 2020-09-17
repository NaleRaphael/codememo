#!/bin/bash
set -e

python -mpytest \
    --cov-config=.coveragerc \
    --cov=codememo \
    ./tests/
