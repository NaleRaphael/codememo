#!/bin/bash
set -e

pytest \
    --cov-config=.coveragerc \
    --cov=codememo \
    ./tests/
