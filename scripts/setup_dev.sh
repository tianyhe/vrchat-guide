#!/bin/bash

# Get absolute path to project root
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# Update PYTHONPATH to include all package sources
export PYTHONPATH="${PROJECT_ROOT}/packages/genie-worksheets:${PROJECT_ROOT}/packages/neu-llm-avatars:${PROJECT_ROOT}/packages/suql/src/suql:${PYTHONPATH}"

# Install spaCy model if not already installed
python -m spacy download en_core_web_sm

# Activate virtual environment
source venv/bin/activate

# Set up any other environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

echo "Development environment configured!"