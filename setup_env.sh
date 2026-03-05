#!/usr/bin/env bash
# simple helper to set up a Python virtual environment for the
# AI Essay Analyst project.  Run this from the repository root.

set -euo pipefail

if [ ! -f requirements.txt ]; then
    echo "cannot find requirements.txt; run this script from project root"
    exit 1
fi

PYTHON=${PYTHON:-python3}

# create virtualenv folder if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv..."
    $PYTHON -m venv .venv
fi

# activate
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "Environment ready. Activate with: source .venv/bin/activate"