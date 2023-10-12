#!/bin/bash

cd "$(dirname "$0")" || exit

# rename venv to .venv if exists
if [ -d "venv" ]; then
    mv venv .venv
fi

source ./.venv/bin/activate
python server.py